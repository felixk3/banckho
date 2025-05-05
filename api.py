from http import HTTPStatus
from typing import List
from fastapi import FastAPI,HTTPException
from databese import session
from models import User,Trasferencia
from sqlalchemy import select
from schema import BaseUsuario,PublicUser,Referencia_Trasferencia
import requests as req


app = FastAPI()


@app.get('/',response_model=List[PublicUser])
def index():
    users = session.scalars(select(User)).all()
    return users


@app.post('/create_user/',status_code=HTTPStatus.CREATED, response_model=PublicUser)
def createuser(user:BaseUsuario):

    create_user = User(
        nome_completo=user.nome_completo,
        saldo=user.saldo, 
        cpf=user.cpf,
        email=user.email,
        senha=user.senha
    )

    session.add(create_user)
    session.commit()
    session.refresh(create_user)

    return   create_user


@app.post('/transferencia/',status_code=HTTPStatus.CREATED)
def transferencia(referencia:Referencia_Trasferencia):

    pagador_userid=session.scalar(select(User).where(User.cpf==referencia.cpf_pagador))
    beneficiario_userid = session.scalar(select(User).where(User.cpf==referencia.cpf_beneficiario))


    if not pagador_userid or not beneficiario_userid:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("Nao existe referencia para essa trasferencia!"))
    
    if pagador_userid.cpf == referencia.cpf_beneficiario:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("Falha na trasferencia! Voce nao pode fazer trasferencia para voce mesmo"))

    if pagador_userid.saldo>referencia.valor:

        #AUTORIZACAO EXTERNA
        authorization = req.get('https://util.devi.tools/api/v2/authorize')

        if (authorization.status_code==HTTPStatus.OK):
    
            pagador_userid.saldo-=referencia.valor
            beneficiario_userid.saldo+=referencia.valor

            session.commit()
            session.refresh(pagador_userid)
            session.commit()
            session.refresh(beneficiario_userid)

            trasfe = Trasferencia(
                valor=referencia.valor,
                pagador_id=pagador_userid.id,
                beneficiario_id=beneficiario_userid.id,
            )

            session.add(trasfe)
            session.commit()
            session.refresh(trasfe)
            
            return {
                'valor':referencia.valor,
                'pagador':referencia.cpf_pagador,
                'beneficiario':referencia.cpf_beneficiario,
            }
        
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("FALHA TRANSACAO NAO AUTORIZADA!"))
    
    else:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("Falha na trasferencia! Saldo Insuficiente"))
    



