from werkzeug.exceptions import BadRequest

from flask import Blueprint, Flask, url_for

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


@bp.route("/item")
def item():
    return "item"


@bp.route("/boom")
def boom():
    raise BadRequest()


app = Flask(__name__)
app.register_blueprint(bp, url_prefix="/api")


# 蓝图自己拒带点 endpoint（用一个还没注册的新蓝图，避开 setup 保护）
probe_bp = Blueprint("probe", __name__)
try:
    probe_bp.add_url_rule("/x", "probe.dotted", lambda: "x")
    print("A1 蓝图带点 endpoint -> 照收（不对）")
except ValueError as exc:
    print("A1 蓝图带点 endpoint -> ValueError:", exc)

# app 级现在同样拒绝带点 endpoint，冒名路由根本进不来
try:
    app.add_url_rule("/lookalike", "api.lookalike", lambda: "lookalike")
    print("A2 app 带点 endpoint -> 照收（不对）")
except ValueError as exc:
    print("A2 app 带点 endpoint -> ValueError:", exc)


@app.route("/plain")
def plain():
    return "plain"


@app.route("/app-boom")
def app_boom():
    raise BadRequest()


c = app.test_client()

ran.clear()
r = c.get("/plain")
print(
    "B1 GET /plain",
    r.status_code,
    "触发 api 蓝图钩子（应为空）:",
    ran,
)

ran.clear()
r = c.get("/app-boom")
print(
    "B2 GET /app-boom（400）",
    r.status_code,
    "（默认 400 页，不被 api 蓝图 errorhandler 接管）",
    "钩子（应为空）:",
    ran,
)

ran.clear()
r = c.get("/api/item")
with app.test_request_context():
    item_url = url_for("api.item")
print(
    "C1 GET /api/item",
    r.status_code,
    "触发 api 蓝图钩子（应为 before+after）:",
    ran,
    "url_for:",
    item_url,
)

ran.clear()
r = c.get("/api/boom")
print(
    "C2 GET /api/boom（400）",
    r.status_code,
    "body=",
    r.get_data(as_text=True),
    "（由 api 蓝图 errorhandler 接管）",
    "钩子:",
    ran,
)

with app.test_request_context("/plain"):
    from flask import request

    print("D1 request.blueprint（应为 None）:", request.blueprint)

with app.test_request_context("/api/item"):
    from flask import request

    print("D2 request.blueprint（应为 api）:", request.blueprint)
