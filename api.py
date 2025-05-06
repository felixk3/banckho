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

    cpf_validar_usuario_existente = session.scalar(
        select(User).where(User.cpf==user.cpf)
    )

    email_validar_usuario_existente = session.scalar(
        select(User).where(User.email==user.email)
    )

    if(cpf_validar_usuario_existente):
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='FALHA NO CADASTRO ESSE CPF JA EXISTE!')
    
    if(email_validar_usuario_existente):
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='FALHA NO CADASTRO ESSE EMAIL JA EXISTE!')

    create_user = User(
        nome_completo=user.nome_completo,
        saldo=user.saldo,
        choice_account=user.escolha,
        cpf=user.cpf,
        email=user.email,
        senha=user.senha
    )

    session.add(create_user)
    session.commit()
    session.refresh(create_user)

    return create_user


@app.post('/transferencia/',status_code=HTTPStatus.CREATED)
def transferencia(referencia:Referencia_Trasferencia):

    pagador_userid=session.scalar(select(User).where(User.cpf==referencia.cpf_pagador))
    beneficiario_userid = session.scalar(select(User).where(User.cpf==referencia.cpf_beneficiario))


    if not pagador_userid or not beneficiario_userid:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("Nao existe referencia para essa trasferencia!"))
    
    if pagador_userid.cpf == referencia.cpf_beneficiario:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("Falha na trasferencia! Voce nao pode fazer trasferencia para voce mesmo"))
    
    if pagador_userid.choice_account == 'lojistas':
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("Falha na trasferencia! Logista nao pode efectuar trasferencia"))

    if pagador_userid.saldo>referencia.valor:

        #AUTORIZACAO EXTERNA
        authorization = req.get('https://util.devi.tools/api/v2/authorize')
        
        #NOTIFICACO EXTERNA
        notificacao = req.post('https://util.devi.tools/api/v1/notify',data={'message': 'Trasferencia bem sucedida'})

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
                'notificacao': "transferencia bem sucedida! Ola voce acabou de transferir dinheiro." if notificacao.status_code == 204 else "trasferencia bem sucedido! Servico de mensageria processando!"
            }
        
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("FALHA TRANSACAO NAO AUTORIZADA!"))
    
    else:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("Falha na trasferencia! Saldo Insuficiente"))
    


