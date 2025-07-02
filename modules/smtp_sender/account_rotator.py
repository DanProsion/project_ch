import random

def choose_account(smtp_accounts, usage_limits=None, max_per_account=10):
    # Исключаем неактивные аккаунты
    candidates = [acc for acc in smtp_accounts if acc.get("active", True)]
    if not candidates:
        return None

    # Фильтрация по лимитам использования
    if usage_limits:
        candidates = [acc for acc in candidates if usage_limits.get(acc["username"], 0) < max_per_account]

    if not candidates:
        return None

    # Сортировка по приоритету (меньшее значение — выше приоритет)
    candidates.sort(key=lambda x: x.get("priority", 10))

    # Получение весов (по умолчанию = 1.0)
    weights = [acc.get("weight", 1.0) for acc in candidates]

    # Выбор с учётом весов
    selected = random.choices(candidates, weights=weights, k=1)[0]
    return selected
