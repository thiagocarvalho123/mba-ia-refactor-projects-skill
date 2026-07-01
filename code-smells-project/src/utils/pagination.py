from src.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


def parse_pagination(request):
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = min(max(int(request.args.get("per_page", DEFAULT_PAGE_SIZE)), 1), MAX_PAGE_SIZE)
    except (TypeError, ValueError):
        per_page = DEFAULT_PAGE_SIZE
    return page, per_page
