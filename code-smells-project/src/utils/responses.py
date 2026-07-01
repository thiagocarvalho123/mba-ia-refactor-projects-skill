from flask import jsonify


def success(dados=None, mensagem=None, status=200, extra=None):
    body = {"sucesso": True}
    if dados is not None:
        body["dados"] = dados
    if mensagem is not None:
        body["mensagem"] = mensagem
    if extra:
        body.update(extra)
    return jsonify(body), status


def error(mensagem, status=400):
    return jsonify({"sucesso": False, "erro": mensagem}), status
