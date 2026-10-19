from flask import Flask, render_template, jsonify, request
from datetime import datetime
from threading import Lock

app = Flask(__name__)
lock = Lock()

state = {
    "devices": {
        "living_light": {"name": "Living Room Light", "room": "Living Room", "kind": "light", "online": True, "on": True, "watts": 12},
        "bedroom_light": {"name": "Bedroom Light", "room": "Bedroom", "kind": "light", "online": True, "on": False, "watts": 9},
        "smart_fan": {"name": "Smart Fan", "room": "Living Room", "kind": "fan", "online": True, "on": True, "watts": 45},
        "air_purifier": {"name": "Air Purifier", "room": "Bedroom", "kind": "air", "online": True, "on": False, "watts": 32},
    },
    "automation": True,
    "security": True,
    "logs": []
}

def add_log(message, category="system"):
    state["logs"].insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "message": message, "category": category})
    state["logs"] = state["logs"][:12]

add_log("Smart Home dashboard initialized", "system")
add_log("Local network simulation ready", "network")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/state")
def get_state():
    with lock:
        devices = state["devices"]
        active = sum(1 for d in devices.values() if d["online"] and d["on"])
        online = sum(1 for d in devices.values() if d["online"])
        power = sum(d["watts"] for d in devices.values() if d["online"] and d["on"])
        return jsonify({"devices": devices, "automation": state["automation"], "security": state["security"], "logs": state["logs"], "metrics": {"online": online, "total": len(devices), "active": active, "power": power}})

@app.route("/api/device/<device_id>/toggle", methods=["POST"])
def toggle_device(device_id):
    with lock:
        device = state["devices"].get(device_id)
        if not device:
            return jsonify({"error": "Unknown device"}), 404
        if not device["online"]:
            return jsonify({"error": "Device is offline"}), 409
        device["on"] = not device["on"]
        add_log(f"{device['name']} turned {'on' if device['on'] else 'off'}", "device")
        return jsonify({"ok": True, "on": device["on"]})

@app.route("/api/automation", methods=["POST"])
def toggle_automation():
    with lock:
        state["automation"] = bool(request.json.get("enabled", False))
        add_log(f"Automation {'enabled' if state['automation'] else 'disabled'}", "system")
        return jsonify({"ok": True, "enabled": state["automation"]})

@app.route("/api/security", methods=["POST"])
def toggle_security():
    with lock:
        state["security"] = bool(request.json.get("enabled", False))
        add_log(f"Security monitoring {'enabled' if state['security'] else 'disabled'}", "security")
        return jsonify({"ok": True, "enabled": state["security"]})

@app.route("/api/scene/<scene_name>", methods=["POST"])
def scene(scene_name):
    scenes = {
        "away": {"living_light": False, "bedroom_light": False, "smart_fan": False, "air_purifier": False},
        "relax": {"living_light": True, "bedroom_light": False, "smart_fan": True, "air_purifier": False},
        "night": {"living_light": False, "bedroom_light": True, "smart_fan": False, "air_purifier": True},
    }
    if scene_name not in scenes:
        return jsonify({"error": "Unknown scene"}), 404
    with lock:
        for key, on in scenes[scene_name].items():
            state["devices"][key]["on"] = on
        add_log(f"'{scene_name.title()}' scene applied", "automation")
        return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
