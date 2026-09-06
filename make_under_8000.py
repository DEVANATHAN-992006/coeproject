with open("final_report_strict_under_8k.txt", "r", encoding="utf-8") as f:
    t = f.read()

t = t.replace("System correctness is verified by an automated Pytest suite of 14 test cases (all pass).", "System correctness is verified by a Pytest suite of 14 test cases (all pass).")
t = t.replace("The current 35% implementation establishes the core foundation of MEDIROUTE.", "The current 35% implementation establishes the foundation of MEDIROUTE.")

print("Final length:", len(t))
with open("final_report_strict_under_8k.txt", "w", encoding="utf-8") as f:
    f.write(t)
