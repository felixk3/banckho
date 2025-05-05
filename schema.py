from pydantic import BaseModel,EmailStr



class BaseUsuario(BaseModel):
    nome_completo:str
    saldo:int
    cpf:int
    email:EmailStr
    senha:str

class PublicUser(BaseModel):
    id:int
    nome_completo:str
    saldo:int
    cpf:int
    email:EmailStr


class Referencia_Trasferencia(BaseModel):
    valor:int
    cpf_pagador:int
    cpf_beneficiario:int


"""

class Usuario(BaseUsuario):
    id:int


class PassUsuario(BaseUsuario):
    
"""    
