extends "res://addons/gdUnit4/src/GdUnitTestSuite.gd"

const _REPORT_FILENAME := "signal-contracts.json"

var _evt := {}
var _http_blocked := {}

func _today_dir() -> String:
    var d = Time.get_date_dict_from_system()
    return "%04d-%02d-%02d" % [d.year, d.month, d.day]

func _write_report(report: Dictionary) -> void:
    var ymd = _today_dir()
    var out_dir = "user://e2e/%s/security" % ymd
    DirAccess.make_dir_recursive_absolute(out_dir)
    var out_path = out_dir + "/" + _REPORT_FILENAME
    var f = FileAccess.open(out_path, FileAccess.WRITE)
    if f:
        f.store_string(JSON.stringify(report, "  "))
        f.flush()
        f.close()
    print("SIGNAL_CONTRACTS_OUT:", ProjectSettings.globalize_path(out_path))

func _on_domain_event_emitted(type, source, data_json, id, spec, ct, ts) -> void:
    _evt = {
        "type": str(type),
        "source": str(source),
        "data_json": str(data_json),
        "id": str(id),
        "specversion": str(spec),
        "datacontenttype": str(ct),
        "time": str(ts),
    }

func _on_http_blocked(reason, url) -> void:
    _http_blocked = {
        "reason": str(reason),
        "url": str(url),
    }

func _check_event_bus_signal() -> Dictionary:
    var r := {
        "name": "EventBusAdapter.DomainEventEmitted",
        "ok": false,
        "errors": [],
        "observed": {},
    }

    var bus: Node = load("res://Game.Godot/Adapters/EventBusAdapter.cs").new()
    add_child(auto_free(bus))

    if not bus.has_signal("DomainEventEmitted"):
        r["errors"].append("missing signal DomainEventEmitted")
        return r

    _evt = {}
    bus.connect("DomainEventEmitted", Callable(self, "_on_domain_event_emitted"), CONNECT_ONE_SHOT)

    if not bus.has_method("PublishSimple"):
        r["errors"].append("missing method PublishSimple")
        return r

    bus.PublishSimple("core.contract.signal.emitted", "gdunit", "{}")
    await get_tree().process_frame

    if _evt.is_empty():
        r["errors"].append("signal not emitted")
        return r

    r["observed"] = _evt

    var ok := true
    if str(_evt.get("type", "")) != "core.contract.signal.emitted":
        ok = false
        r["errors"].append("type mismatch")
    if str(_evt.get("source", "")) != "gdunit":
        ok = false
        r["errors"].append("source mismatch")
    if str(_evt.get("data_json", "")) != "{}":
        ok = false
        r["errors"].append("data_json mismatch")
    if str(_evt.get("id", "")) == "":
        ok = false
        r["errors"].append("id empty")
    if str(_evt.get("specversion", "")) != "1.0":
        ok = false
        r["errors"].append("specversion mismatch")
    if str(_evt.get("datacontenttype", "")) != "application/json":
        ok = false
        r["errors"].append("datacontenttype mismatch")
    if str(_evt.get("time", "")) == "":
        ok = false
        r["errors"].append("time empty")

    r["ok"] = ok
    return r

func _check_security_http_client_signal() -> Dictionary:
    var r := {
        "name": "SecurityHttpClient.RequestBlocked",
        "ok": false,
        "errors": [],
        "observed": {},
    }

    var http: Node = load("res://Game.Godot/Scripts/Security/SecurityHttpClient.cs").new()
    add_child(auto_free(http))

    if not http.has_signal("RequestBlocked"):
        r["errors"].append("missing signal RequestBlocked")
        return r

    if not http.has_method("Validate"):
        r["errors"].append("missing method Validate")
        return r

    _http_blocked = {}
    http.connect("RequestBlocked", Callable(self, "_on_http_blocked"), CONNECT_ONE_SHOT)

    var ok: bool = http.Validate("GET", "http://example.com")
    await get_tree().process_frame

    if ok:
        r["errors"].append("expected Validate() to return false")
    if _http_blocked.is_empty():
        r["errors"].append("signal not emitted")
        return r

    r["observed"] = _http_blocked

    var reason: String = str(_http_blocked.get("reason", ""))
    var url: String = str(_http_blocked.get("url", ""))
    if url != "http://example.com":
        r["errors"].append("url mismatch")
    if reason == "":
        r["errors"].append("reason empty")

    r["ok"] = r["errors"].is_empty()
    return r

func test_signal_contracts_security_sensitive() -> void:
    var checks: Array = []
    checks.append(await _check_event_bus_signal())
    checks.append(await _check_security_http_client_signal())

    var failed := 0
    for c in checks:
        if not bool(c.get("ok", false)):
            failed += 1

    var report := {
        "ts": Time.get_datetime_string_from_system(true),
        "project": "Tests.Godot",
        "checks": checks,
        "summary": {
            "passed": checks.size() - failed,
            "failed": failed,
        },
    }

    _write_report(report)
    assert_int(failed).is_equal(0)
