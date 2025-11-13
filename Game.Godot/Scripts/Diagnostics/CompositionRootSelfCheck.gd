extends SceneTree

func _init() -> void:
    call_deferred("_run")

func _run() -> void:

    var result := {
        "ts": Time.get_datetime_string_from_system(true),
        "ports": {
            "time": false,
            "input": false,
            "resourceLoader": false,
            "dataStore": false,
            "logger": false,
            "eventBus": false,
        }
    }

    var cr := root.get_node_or_null("/root/CompositionRoot")
    if cr == null:
        result["error"] = "CompositionRoot not found (autoload not configured)"
        _write_and_quit(result)
        return

    # time
    result["ports"]["time"] = cr.Time != null

    # input
    var input_ok := false
    if cr.Input != null and cr.Input.has_method("IsPressed"):
        var _p = cr.Input.IsPressed("ui_accept")
        input_ok = true
    result["ports"]["input"] = input_ok

    # resource loader (read project.godot)
    var res_ok := false
    if cr.ResourceLoader != null and cr.ResourceLoader.has_method("LoadText"):
        var txt = cr.ResourceLoader.LoadText("res://project.godot")
        res_ok = txt != null and txt.length() > 0
    result["ports"]["resourceLoader"] = res_ok

    # data store (user://)
    var store_ok := false
    if cr.DataStore != null and cr.DataStore.has_method("SaveSync"):
        var key = "selfcheck-" + str(Time.get_unix_time_from_system())
        var payload = "{\"ok\":true}"
        cr.DataStore.SaveSync(key, payload)
        var loaded = cr.DataStore.LoadSync(key)
        cr.DataStore.DeleteSync(key)
        store_ok = loaded == payload
    result["ports"]["dataStore"] = store_ok

    # logger
    var logger_ok := false
    if cr.Logger != null and cr.Logger.has_method("Info"):
        cr.Logger.Info("composition-root-selfcheck")
        logger_ok = true
    result["ports"]["logger"] = logger_ok

    # event bus (minimal publish)
    var bus_ok := false
    if cr.EventBus != null and cr.EventBus.has_method("PublishSimple"):
        cr.EventBus.PublishSimple("selfcheck.ok", "CompositionRootSelfCheck", "{}")
        bus_ok = true
    result["ports"]["eventBus"] = bus_ok

    _write_and_quit(result)

func _write_and_quit(result: Dictionary) -> void:
    var d = Time.get_date_dict_from_system()
    var ymd = "%04d-%02d-%02d" % [d.year, d.month, d.day]
    var out_dir = "user://e2e/%s" % ymd
    DirAccess.make_dir_recursive_absolute(out_dir)
    var out_path = out_dir + "/composition_root_selfcheck.json"
    var f = FileAccess.open(out_path, FileAccess.WRITE)
    if f:
        f.store_string(JSON.stringify(result))
        f.flush()
        f.close()
    print("SELF_CHECK_OUT:", ProjectSettings.globalize_path(out_path))
    quit()
