from http import HTTPStatus
from typing import List
from fastapi import Depends, FastAPI,HTTPException
from databese import get_session
from models import User,Trasferencia
from sqlalchemy import select
from security import get_password_hash
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from schema import BaseUsuario,PublicUser,Referencia_Trasferencia,Token
from fastapi.security import OAuth2PasswordRequestForm
from security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
)
import requests as req

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

@app.post('/token', response_model=Token)
def login_for_access_token(
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = session.scalar(select(User).where(User.email == form_data.username))

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect email or password'
        )

    if not verify_password(form_data.password, user.senha):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect email or password'
        )

    access_token = create_access_token(data={'sub': user.email})

    return {'access_token': access_token, 'token_type': 'bearer'}



@app.get('/',response_model=List[PublicUser])
def index(session: Session = Depends(get_session),current_user: User = Depends(get_current_user)):
    users = session.scalars(select(User)).all()
    return users



@app.post('/create_user/',status_code=HTTPStatus.CREATED, response_model=PublicUser)
def createuser(user:BaseUsuario,session: Session = Depends(get_session)):

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
        senha=get_password_hash(user.senha)
    )

    session.add(create_user)
    session.commit()
    session.refresh(create_user)
    session.close()

    return create_user


@app.post('/transferencia/',status_code=HTTPStatus.CREATED)
def transferencia(referencia:Referencia_Trasferencia,session: Session = Depends(get_session),current_user: User = Depends(get_current_user)):

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
            session.close()


            return {
                'valor':referencia.valor,
                'pagador':referencia.cpf_pagador,
                'beneficiario':referencia.cpf_beneficiario,
                'notificacao': "transferencia bem sucedida! Ola voce acabou de transferir dinheiro." if notificacao.status_code == 204 else "trasferencia bem sucedido! Servico de mensageria processando!"
            }
        
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("FALHA TRANSACAO NAO AUTORIZADA!"))
    
    else:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,detail=("Falha na trasferencia! Saldo Insuficiente"))
    


