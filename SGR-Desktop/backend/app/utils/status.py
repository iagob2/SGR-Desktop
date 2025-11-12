def is_status_concluido(status) -> bool:
    """
    Verifica se um status é considerado concluído/finalizado.
    Aceita apenas: FINALIZADO, CONCLUIDO, CONCLUÍDO, ENTREGUE (variações inclusas).
    """
    if not status:
        return False

    status_normalizado = str(status).strip().upper()

    status_concluidos = [
        'FINALIZADO',
        'FINALIZADA',
        'FINALIZADOS',
        'FINALIZADAS',
        'CONCLUIDO',
        'CONCLUÍDO',
        'CONCLUIDA',
        'CONCLUÍDA',
        'CONCLUIDOS',
        'CONCLUÍDOS',
        'CONCLUIDAS',
        'CONCLUÍDAS',
        'ENTREGUE',
        'ENTREGUES',
    ]

    return status_normalizado in status_concluidos


__all__ = ['is_status_concluido']

