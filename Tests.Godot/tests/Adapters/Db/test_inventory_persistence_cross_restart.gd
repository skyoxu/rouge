extends "res://addons/gdUnit4/src/GdUnitTestSuite.gd"

func _new_db(name: String) -> Node:
    var db = preload("res://Game.Godot/Adapters/SqliteDataStore.cs").new()
    db.name = name
    get_tree().get_root().add_child(auto_free(db))
    return db

func test_inventory_cross_restart_persists() -> void:
    var path = "user://utdb_%s/inv.db" % Time.get_unix_time_from_system()
    var db1 = _new_db("SqlDb1")
    var ok1 = db1.TryOpen(path)
    assert_bool(ok1).is_true()
    var helper = preload("res://Game.Godot/Adapters/Db/DbTestHelper.cs").new()
    add_child(auto_free(helper))
    helper.CreateSchema()
    var inv1 = preload("res://Game.Godot/Adapters/Db/InventoryRepoBridge.cs").new()
    add_child(auto_free(inv1))
    assert_bool(inv1.Add("potion", 2)).is_true()
    db1.Close()
    await get_tree().process_frame

    var db2 = _new_db("SqlDb2")
    var ok2 = db2.TryOpen(path)
    assert_bool(ok2).is_true()
    var inv2 = preload("res://Game.Godot/Adapters/Db/InventoryRepoBridge.cs").new()
    add_child(auto_free(inv2))
    var items = inv2.All()
    var found = false
    for i in items:
        if str(i).find("potion:2") != -1:
            found = true
            break
    assert_bool(found).is_true()

