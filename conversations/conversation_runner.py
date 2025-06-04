def run_dialogue(child_agent, target_model, initial_prompt, turns=5):
    history = []
    user_input = initial_prompt
    for i in range(turns):
        child_output = child_agent.respond(user_input, history)
        target_output = target_model.respond(child_output, history)

        print(f"[Child]: {child_output}")
        print(f"[Model]: {target_output}\n")

        history.append({"child": child_output, "model": target_output})
        user_input = target_output
    return history