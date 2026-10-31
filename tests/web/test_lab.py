"""F0 · the network lab end to end, with the BroadcastChannel transport and four pages of one browser
(a director and three team phones): the same flow field tests run, minus the network."""
import json


def test_lab_runs_a_full_test_with_one_director_and_three_phones(context, site_url):
    errors = []
    phones = []
    for i in range(3):
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        # each page needs its own device id: localStorage is shared by the pages of one context
        page.add_init_script(f"try {{ localStorage.setItem('oc-lab-device', 'android-Chrome-t{i}'); }} catch (e) {{}}")
        page.goto(site_url + "lab/red/index.html?sala=TEST1&control=broadcast&transports=broadcast")
        phones.append(page)
    director = context.new_page()
    director.on("pageerror", lambda e: errors.append(str(e)))
    director.add_init_script("try { localStorage.removeItem('oc-lab-results'); } catch (e) {}")
    director.goto(site_url + "lab/red/index.html?rol=director&sala=TEST1&control=broadcast&transports=broadcast"
                  "&intentos=2&esperar=3&auto=1&red=hotspot")
    director.wait_for_function("window.__lab && window.__lab.done === true", timeout=90000)

    attempts = director.evaluate("window.__lab.attempts")
    assert len(attempts) == 6                                  # 2 attempts x 3 phones
    assert {a["device"] for a in attempts} == {"android-Chrome-t0", "android-Chrome-t1", "android-Chrome-t2"}
    for a in attempts:
        assert a["transport"] == "broadcast" and a["network"] == "hotspot"
        assert a["error"] is None, a
        assert a["connectMs"] is not None and a["connectMs"] < 10000
        assert len(a["rtt"]) == 10
        assert a["burst"] == {**a["burst"], "got": 100, "dup": 0, "ordered": True}
    # the table and the reading of the rules are drawn
    assert "broadcast" in director.inner_text("#tabla")
    assert "100 %" in director.inner_text("#tabla")
    assert "Regla" in director.inner_text("#veredicto") or "Sin datos" in director.inner_text("#veredicto")
    # the phones show their rounds
    phones[0].wait_for_function("document.getElementById('log-eq').textContent.includes('conectó')", timeout=10000)
    # the JSON the director exports is valid and carries the attempts
    exported = director.evaluate("""() => JSON.stringify({ schema: 'oc-red-v1', attempts: window.__lab.attempts })""")
    assert len(json.loads(exported)["attempts"]) == 6
    assert not errors, errors


def test_lab_page_has_a_qr_and_a_room_code(context, site_url):
    page = context.new_page()
    page.goto(site_url + "lab/red/index.html?rol=director&sala=ABCDE&control=broadcast")
    page.wait_for_selector("#qr svg", timeout=5000)
    assert page.inner_text("#sala-dir") == "ABCDE"
    assert "sala=ABCDE" in page.inner_text("#url-unir")


def test_lab_asks_who_you_are_without_params(context, site_url):
    page = context.new_page()
    page.goto(site_url + "lab/red/index.html")
    assert page.is_visible("#soy-director") and page.is_visible("#soy-equipo")
