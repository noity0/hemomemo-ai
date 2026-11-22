"""🧪 _t_autonomous.py — Hemomemo AI autonomous engine smoke tests (pure stdlib)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import autonomous as A


def show(q):
    r = A.answer(q)
    print("-" * 70)
    print("Q:", q)
    print("  kind=%s source=%s conf=%.2f verified=%s" % (r.get("kind"), r.get("source"),
                                                         r.get("confidence") or 0.0, r.get("verified")))
    print("  ANSWER:", (r.get("answer") or "")[:300])
    print("  steps:", r.get("steps") or [])
    print("  uncertainty:", r.get("uncertainty"), "| sources:", r.get("sources"))


if __name__ == "__main__":
    print("== CLASSIFY ==")
    for q in ["photosynthesis kya hai aur kyun zaruri hai",
              "12 * 4 + 3",
              "salam",
              "tumhara owner kaun hai",
              "allah kya hai",
              "xyzqwertyuiop test sawal",
              "2 aur 3 ka total kya hai",
              "kitna hai 12 aur 8 ka farq",
              "17 saal ka kya matlab hai",
              "how photosynthesis work"]:
        print("   ", q, "->", A.classify(q))

    print("== MATH ==")
    for q in ["12 * 4 + 3", "100 / 5", "2 aur 3 ka total kya hai", "kitna hai 12 aur 8 ka farq"]:
        ans, steps, conf, ver, tags = A.math_answer(q)
        print("   MATH Q=%r -> ans=%r steps=%s conf=%s ver=%s tags=%s" % (q, ans, steps, conf, ver, tags))

    print("== ANSWERS ==")
    show("salam")
    show("tumhara owner kaun hai")
    show("allah kya hai")
    show("photosynthesis kya hai")
    show("xyzqwertyuiop test sawal")

    # 🧹 KACHRA-INPUT GUARD: junk par wahi greeting spam NAHI honi chahiye
    for junk in ["fdsf", "wtf", "xyzqwerty"]:
        r = A.answer(junk)
        assert r.get("kind") == "unknown", "junk %r -> %s" % (junk, r.get("kind"))
        assert "Assalamu Alaikum" not in (r.get("answer") or ""), "junk %r ko greeting!" % junk
        assert r.get("source") in ("imandari", "live-research")
    print("[GUARD-OK] junk inputs → imandari honest jawab (greeting spam nahi)")

    # 🧠 SAMAJH-CORE GUARD (aqal upgrade): hi/hiiii/byeeee/okkk/ho saath hi
    #    social-intent mazboot hain — koi imandari "pura ilm nahi" dump NAHI
    for q, exp_social, exp_in in [
        ("hii", "greet", "Salam"),
        ("hiiii", "greet", "Salam"),
        ("byeeee", "farewell", "Allah hafiz"),
        ("okkk", "ack", "Ji"),
        ("ho", "bolo", "main sun"),
    ]:
        r = A.answer(q)
        assert r.get("social") == exp_social, (q, r.get("social"))
        assert exp_in in (r.get("answer") or ""), (q, r.get("answer"))
    print("[GUARD-OK] SAMAJH: hii/hiiii->greet, byeeee->farewell, okkk->ack, ho->bolo")

    # 📐 FORMULA-LIBRARY GUARDS (math+physics A-Z plug-and-solve)
    r = A.answer("circle ka area nikaalo r = 5")
    assert r.get("kind") == "math" and (r.get("answer") or "").startswith("Jawab: A = 78.539"), r.get("answer")
    r = A.answer("force nikaalo m = 10 aur a = 3")
    assert r.get("source") == "formula-library" and "30" in (r.get("answer") or ""), r.get("answer")
    r = A.answer("E = mc^2, m = 2")
    assert "1.798" in (r.get("answer") or ""), r.get("answer")
    r = A.answer("simple interest 5000 par 5 percent 2 saal")
    assert "500" in (r.get("answer") or ""), r.get("answer")
    r = A.answer("triangle ka area, b = 10 aur h = 4")
    assert "20" in (r.get("answer") or ""), r.get("answer")
    print("[GUARD-OK] FORMULA-LIBRARY: circle/force/emc2/interest/triangle plug-and-solve")

    # ➗ HAR-OPERATOR GUARDS (x × ÷ ^ // ! sqrt percent words)
    r = A.answer("12 x 4")
    assert r.get("kind") == "math" and "48" in (r.get("answer") or ""), r.get("answer")
    r = A.answer("2^10")
    assert "1024" in (r.get("answer") or ""), r.get("answer")
    r = A.answer("sqrt(144)")
    assert r.get("kind") == "math" and "12" in (r.get("answer") or ""), r.get("answer")
    r = A.answer("10 // 3")
    assert (r.get("answer") or "").startswith("Jawab: 3"), r.get("answer")
    r = A.answer("5!")
    assert "120" in (r.get("answer") or ""), r.get("answer")
    r = A.answer("20 percent of 50")
    assert "10" in (r.get("answer") or ""), r.get("answer")
    r = A.answer("16 ka square root")
    assert "4" in (r.get("answer") or ""), r.get("answer")
    r = A.answer("100 taqseem 4")
    assert "25" in (r.get("answer") or ""), r.get("answer")
    print("[GUARD-OK] OPERATORS: x ^ sqrt // ! percent-words taqseem sab chale")

    # 🚫 FORMULA-GATE: normal baat-cheet me formula-library NAHI khulti —
    # (kaam/tension/speed/energy/power jaise rozmarra lafz math nahi hain)
    for q in ("tension na lo yaar", "mujhe apni life me speed chahiye",
              "ek kaam batao", "meri energy khatam ho gayi",
              "5 baje milte hain", "volume kam karo TV ka"):
        r = A.answer(q)
        ans = (r.get("answer") or "")
        assert not (r.get("kind") == "math"
                    and ("Formula" in ans or "formula:" in str(r.get("source")))), \
            (q, r.get("kind"), r.get("source"), ans[:70])
    print("[GUARD-OK] FORMULA-GATE: normal chat me formula nahi (sirf math sawal)")

    # 🫀 FEELINGS GUARD: mood/energy/sensors chamakte hain
    from model import feelings as F
    s0 = F.sensors()
    for _k in range(5):
        F.senses("zigzuq_marud")
    s1 = F.sensors()
    assert s1["turns"] > s0["turns"], "baatein count nahi hui"
    print("[GUARD-OK] feelings/sensors: %s → %s (turns %d→%d)"
          % (s0["mood"], s1["mood"], s0["turns"], s1["turns"]))
    print("    ", F.status_line())

    # 🤝 GREETING GUARD: asli salam abhi bhi adab jawab deta hai
    r = A.answer("salam")
    assert r.get("kind") == "chit-chat" and "Assalamu Alaikum" in (r.get("answer") or "")
    print("[GUARD-OK] 'salam' → adab greeting salamat")

    print("== CHAT WRAPPER ==")
    txt, rep = A.chat("12 * 4 + 3")
    print(txt, "| source:", rep.get("source"), "| conf:", rep.get("confidence"))
    txt, rep = A.chat("salam")
    print(txt, "| source:", rep.get("source"))
