from app.extraction.postgres import normalize_table_facts

# Build payload2 step by step to avoid nested bracket issues
inner = [["Metric", "1984-85"], ["Production", "12,400"]]
middle = [inner]
payload2 = {"tables": middle}

comp2, partial2 = normalize_table_facts(payload2, "doc", "1-3")
print(f"completed: {len(comp2)}, partial: {len(partial2)}")
for c in comp2:
    print(f"  completed: entity={c.entity}, metric={c.metric}, period={c.period}, value={c.value}, unit={c.unit}")
for p in partial2:
    print(f"  partial: entity={p.entity}, metric={p.metric}, period={p.period}, value={p.value}, unit={p.unit}")