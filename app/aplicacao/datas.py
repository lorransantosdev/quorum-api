from datetime import datetime, timedelta, timezone

FUSO_SP = timezone(timedelta(hours=-3), "America/Sao_Paulo")


def para_utc(valor: datetime | None) -> datetime | None:
    if valor is None:
        return None
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=FUSO_SP)
    return valor.astimezone(timezone.utc)


def para_fuso_sp(valor: datetime) -> datetime:
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(FUSO_SP)
