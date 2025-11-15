extends "res://addons/gdUnit4/src/GdUnitTestSuite.gd"

func _new_db(name: String) -> Node:
    var db = null
    if ClassDB.class_exists("SqliteDataStore"):
        db = ClassDB.instantiate("SqliteDataStore")
    else:
        var s = load("res://Game.Godot/Adapters/SqliteDataStore.cs")
        db = Node.new()
        db.set_script(s)
    db.name = name
    get_tree().get_root().add_child(auto_free(db))
    await get_tree().process_frame
    if not db.has_method("TryOpen"):
        await get_tree().process_frame
    return db

func _today_dir() -> String:
    var d = Time.get_datetime_dict_from_system()
    return "%04d-%02d-%02d" % [d.year, d.month, d.day]

func _read_audit() -> String:
    var p = "res://logs/ci/%s/security-audit.jsonl" % _today_dir()
    if not FileAccess.file_exists(p):
        return ""
    return FileAccess.get_file_as_string(p)

func test_exec_and_query_failures_are_audited() -> void:
    var db = await _new_db("SqlDb")
    # managed path
    var helper = preload("res://Game.Godot/Adapters/Db/DbTestHelper.cs").new()
    add_child(auto_free(helper))
    helper.ForceManaged()
    assert_bool(db.TryOpen("user://utdb_%s/audit.db" % Time.get_unix_time_from_system())).is_true()
    # ensure schema
    db.Execute("CREATE TABLE IF NOT EXISTS x(a INTEGER);")
    # EXEC fail
    var exec_failed := false
    try:
        db.Execute("INSERT INTO non_existing(col) VALUES(1);")
    catch err:
        exec_failed = true
    assert_bool(exec_failed).is_true()
    await get_tree().process_frame
    var content1 = _read_audit()
    assert_str(content1).contains('"action":"db.exec.fail"')
    # QUERY fail
    var query_failed := false
    try:
        db.Query("SELECT * FROM not_a_table;")
    catch err2:
        query_failed = true
    assert_bool(query_failed).is_true()
    await get_tree().process_frame
    var content2 = _read_audit()
    assert_str(content2).contains('"action":"db.query.fail"')

