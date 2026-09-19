from flask import Blueprint, Flask

bp = Blueprint("api", __name__)
ran = []


@bp.before_request
def _b():
    ran.append("api.before")


@bp.after_request
def _a(r):
    ran.append("api.after")
    return r


@bp.errorhandler(400)
def _e400(e):
    return "handled-by-api-blueprint", 200


app = Flask(__name__)
app.register_blueprint(bp, url_prefix="/api")


# 蓝图自己拒带点 endpoint（用一个还没注册的新蓝图，避开 setup 保护）
probe_bp = Blueprint("probe", __name__)
try:
    probe_bp.add_url_rule("/x", "probe.dotted", lambda: "x")
    print("A1 蓝图带点 endpoint -> 照收（不对）")
except ValueError as exc:
    print("A1 蓝图带点 endpoint -> ValueError:", exc)

# app 级不校验带点 endpoint，注册成 api.* 伪装成蓝图成员
app.add_url_rule("/lookalike", "api.lookalike", lambda: "lookalike")
app.add_url_rule("/boom", "api.boom", lambda: (_ for _ in ()).throw(__import__("werkzeug.exceptions").BadRequest()))

c = app.test_client()
ran.clear()
r = c.get("/lookalike")
print("A2 app 带点 endpoint -> 照收不校验；GET /lookalike", r.status_code, "触发 api 蓝图钩子:", ran)
ran.clear()
r = c.get("/boom")
print("GET /boom（400）", r.status_code, "body=", r.get_data(as_text=True), "（本应默认 400 页，却由 api 蓝图 errorhandler 接管）", "钩子:", ran)

with app.test_request_context("/lookalike"):
    from flask import request
    print("request.blueprint 冒出假名:", request.blueprint, "（该 endpoint 并未真属 api 蓝图）")
