from arcade.key import H, MOD_SHIFT, Q

from charm.lib.keymap import keymap

def test_keymap_unbind() -> None:
    assert keymap.debug_toggle_hit_window in keymap.keys[(H, MOD_SHIFT)]
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    keymap.unbind((H, MOD_SHIFT))
    assert keymap.debug_toggle_hit_window not in keymap.keys[(H, MOD_SHIFT)]
    assert (H, MOD_SHIFT) not in keymap.debug_toggle_hit_window.keys

def test_keymap_unbindall() -> None:
    assert keymap.debug_toggle_hit_window in keymap.keys[(H, MOD_SHIFT)]
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    keymap.unbind_all()
    assert len(keymap.keys) == 0
    assert len(keymap.debug_toggle_hit_window.keys) == 0

def test_keymap_setdefaults() -> None:
    assert keymap.debug_toggle_hit_window in keymap.keys[(H, MOD_SHIFT)]
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    keymap.unbind_all()
    assert len(keymap.keys) == 0
    assert len(keymap.debug_toggle_hit_window.keys) == 0
    keymap.set_defaults()
    assert keymap.debug_toggle_hit_window in keymap.keys[(H, MOD_SHIFT)]
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys

def test_pressed() -> None:
    assert not keymap.debug_toggle_hit_window.pressed
    keymap.on_key_press(H, MOD_SHIFT)
    assert keymap.debug_toggle_hit_window.pressed
    keymap.on_key_press(Q, 0)
    assert not keymap.debug_toggle_hit_window.pressed

def test_released() -> None:
    assert not keymap.debug_toggle_hit_window.released
    keymap.on_key_press(H, MOD_SHIFT)
    assert not keymap.debug_toggle_hit_window.released
    keymap.on_key_release(H, MOD_SHIFT)
    assert keymap.debug_toggle_hit_window.released
    keymap.on_key_release(Q, 0)
    assert not keymap.debug_toggle_hit_window.released

def test_held() -> None:
    assert not keymap.debug_toggle_hit_window.held
    keymap.on_key_press(H, MOD_SHIFT)
    assert keymap.debug_toggle_hit_window.held
    keymap.on_key_press(Q, 0)
    assert keymap.debug_toggle_hit_window.held
    keymap.on_key_release(H, MOD_SHIFT)
    assert not keymap.debug_toggle_hit_window.held
    keymap.on_key_release(Q, 0)
    assert not keymap.debug_toggle_hit_window.held

def test_action_v_missing() -> None:
    assert not keymap.start.v_missing
    keymap.start.unbind_all()
    assert keymap.start.v_missing

def test_action_v_toomany() -> None:
    assert not keymap.navleft.v_toomany
    keymap.navleft.bind(Q)
    assert keymap.navleft.v_toomany

def test_action_v_conflict() -> None:
    assert not keymap.start.v_conflict
    assert not keymap.navleft.v_conflict
    keymap.start.bind(Q)
    assert not keymap.start.v_conflict
    assert not keymap.navleft.v_conflict
    keymap.navleft.bind(Q)
    assert keymap.start.v_conflict
    assert keymap.navleft.v_conflict
    keymap.start.unbind(Q)
    assert not keymap.start.v_conflict
    assert not keymap.navleft.v_conflict

def test_action_bind() -> None:
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    assert len(keymap.debug_toggle_hit_window.keys) == 1
    keymap.debug_toggle_hit_window.bind(Q)
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    assert (Q, 0) in keymap.debug_toggle_hit_window.keys
    assert len(keymap.debug_toggle_hit_window.keys) == 2
    keymap.debug_toggle_hit_window.bind(Q)
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    assert (Q, 0) in keymap.debug_toggle_hit_window.keys
    assert len(keymap.debug_toggle_hit_window.keys) == 2

def test_action_unbind() -> None:
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    assert len(keymap.debug_toggle_hit_window.keys) == 1
    keymap.debug_toggle_hit_window.unbind(Q)
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    assert len(keymap.debug_toggle_hit_window.keys) == 1
    keymap.debug_toggle_hit_window.unbind((H, MOD_SHIFT))
    assert len(keymap.debug_toggle_hit_window.keys) == 0
    keymap.debug_toggle_hit_window.unbind((H, MOD_SHIFT))
    assert len(keymap.debug_toggle_hit_window.keys) == 0

def test_action_unbind_all() -> None:
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    assert len(keymap.debug_toggle_hit_window.keys) == 1
    keymap.debug_toggle_hit_window.unbind_all()
    assert len(keymap.debug_toggle_hit_window.keys) == 0
    keymap.debug_toggle_hit_window.unbind_all()
    assert len(keymap.debug_toggle_hit_window.keys) == 0

def test_action_set_defaults() -> None:
    keymap.debug_toggle_hit_window.unbind_all()
    assert len(keymap.debug_toggle_hit_window.keys) == 0
    keymap.debug_toggle_hit_window.set_defaults()
    assert (H, MOD_SHIFT) in keymap.debug_toggle_hit_window.keys
    assert len(keymap.debug_toggle_hit_window.keys) == 1
