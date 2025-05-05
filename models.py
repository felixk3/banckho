from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from sqlalchemy import ForeignKey
from sqlalchemy import String


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_completo: Mapped[str] = mapped_column(String(80))
    saldo:Mapped[int] = mapped_column()
    cpf:Mapped[int] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(String(180),unique=True)
    senha: Mapped[str] = mapped_column(String(15))

    def __repr__(self) -> str:
        return f"User(nome_completo={self.nome_completo!r}, email={self.email!r},saldo={self.saldo!r},cpf={self.cpf!r})"


class Trasferencia(Base):
    __tablename__ = "trasferencia_user"

    id: Mapped[int] = mapped_column(primary_key=True)

    valor:Mapped[int] = mapped_column()

    #ARMAZENAR ID
    pagador_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    beneficiario_id:Mapped[int] = mapped_column(ForeignKey("user_account.id"))

    #ACESSAR OBJECTOS
    pagador: Mapped["User"] = relationship(foreign_keys=[pagador_id])
    beneficiario: Mapped["User"] = relationship(foreign_keys=[beneficiario_id])

