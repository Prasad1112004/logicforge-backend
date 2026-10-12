from __future__ import annotations

ALLOWED_COMMANDS = {
    "move",
    "turn_left",
    "turn_right",
    "jump",
    "collect",
    "wait",
}


def normalize_instruction(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_")


def execute_visual_program(instructions: list[str], maze: dict | None = None) -> dict:
    if not isinstance(instructions, list) or not instructions:
        raise ValueError("A visual program requires at least one instruction.")

    normalized = []
    for instruction in instructions:
        cleaned = normalize_instruction(instruction)
        if cleaned not in ALLOWED_COMMANDS:
            raise ValueError(f"Unsupported instruction: {instruction}")
        normalized.append(cleaned)

    maze_data = maze or {
        "start": (0, 0),
        "goal": (2, 2),
        "grid": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
    }

    start = maze_data.get("start", (0, 0))
    direction = "right"
    x, y = start
    trace = [{"step": 0, "x": x, "y": y, "direction": direction, "instruction": "start"}]

    for step_number, instruction in enumerate(normalized, start=1):
        if instruction == "turn_left":
            direction = {"up": "left", "left": "down", "down": "right", "right": "up"}[direction]
            trace.append({"step": step_number, "x": x, "y": y, "direction": direction, "instruction": instruction})
            continue

        if instruction == "turn_right":
            direction = {"up": "right", "right": "down", "down": "left", "left": "up"}[direction]
            trace.append({"step": step_number, "x": x, "y": y, "direction": direction, "instruction": instruction})
            continue

        if instruction == "move":
            dx, dy = {"up": (0, -1), "right": (1, 0), "down": (0, 1), "left": (-1, 0)}[direction]
            x += dx
            y += dy
            trace.append({"step": step_number, "x": x, "y": y, "direction": direction, "instruction": instruction})
            continue

        if instruction == "jump":
            dx, dy = {"up": (0, -1), "right": (1, 0), "down": (0, 1), "left": (-1, 0)}[direction]
            x += dx * 2
            y += dy * 2
            trace.append({"step": step_number, "x": x, "y": y, "direction": direction, "instruction": instruction})
            continue

        if instruction == "wait":
            trace.append({"step": step_number, "x": x, "y": y, "direction": direction, "instruction": instruction})
            continue

        if instruction == "collect":
            trace.append({"step": step_number, "x": x, "y": y, "direction": direction, "instruction": instruction, "collected": True})

    final_position = (x, y)
    return {
        "final_position": final_position,
        "direction": direction,
        "trace": trace,
        "success": final_position == tuple(maze_data.get("goal", (2, 2))),
    }


def validate_path_matches(program: list[str], expected_path: list[str] | None) -> bool:
    if expected_path is None:
        return False
    provided = [normalize_instruction(item) for item in program]
    expected = [normalize_instruction(item) for item in expected_path]
    return provided == expected
