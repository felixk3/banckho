from pydantic import BaseModel,EmailStr,Field
from models import Choice_Account



class BaseUsuario(BaseModel):
    nome_completo:str
    saldo:int
    escolha:Choice_Account = Field(default=Choice_Account.comuns)
    cpf:int
    email:EmailStr
    senha:str

class PublicUser(BaseModel):
    id:int
    nome_completo:str
    saldo:int
    escolha:Choice_Account = Field(default=Choice_Account.comuns)
    cpf:int
    email:EmailStr


class Referencia_Trasferencia(BaseModel):
    valor:int
    cpf_pagador:int
    cpf_beneficiario:int

class Token(BaseModel):
    access_token: str
    token_type: str