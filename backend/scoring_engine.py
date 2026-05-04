import json

class ScoringEngine:
    def process_action(self, state: dict, action: str, team: str) -> dict:
        raise NotImplementedError

    def is_finished(self, state: dict) -> bool:
        raise NotImplementedError

    def get_winner(self, state: dict) -> int:
        # Returns 1 for Team A, 2 for Team B, 0 for None
        raise NotImplementedError

class Basket3x3Engine(ScoringEngine):
    def get_default_state(self):
        return {
            "score_A": 0,
            "score_B": 0,
            "status": "ongoing" # ongoing, finished
        }

    def process_action(self, state: dict, action: str, team: str) -> dict:
        if state["status"] == "finished":
            return state

        points = 0
        if action == "ADD_1": points = 1
        elif action == "ADD_2": points = 2
        elif action == "SUB_1": points = -1

        if team == "A":
            state["score_A"] = max(0, state["score_A"] + points)
        elif team == "B":
            state["score_B"] = max(0, state["score_B"] + points)

        if state["score_A"] >= 21 or state["score_B"] >= 21:
            state["status"] = "finished"

        return state

    def is_finished(self, state: dict) -> bool:
        return state.get("status") == "finished"

    def get_winner(self, state: dict) -> int:
        if state["score_A"] > state["score_B"]: return 1
        elif state["score_B"] > state["score_A"]: return 2
        return 0

class TenisMejaEngine(ScoringEngine):
    # Best of 5 by default
    def get_default_state(self):
        return {
            "sets_A": 0,
            "sets_B": 0,
            "score_A": 0,
            "score_B": 0,
            "history": [], # [{"A": 11, "B": 8}, ...]
            "status": "ongoing",
            "target_sets": 3 # Win 3 sets to win match (Best of 5)
        }

    def process_action(self, state: dict, action: str, team: str) -> dict:
        if state["status"] == "finished": return state

        if action == "ADD_1":
            if team == "A": state["score_A"] += 1
            elif team == "B": state["score_B"] += 1
        elif action == "SUB_1":
            if team == "A": state["score_A"] = max(0, state["score_A"] - 1)
            elif team == "B": state["score_B"] = max(0, state["score_B"] - 1)

        # Check set win condition (11 points, win by 2)
        sA = state["score_A"]
        sB = state["score_B"]
        if (sA >= 11 or sB >= 11) and abs(sA - sB) >= 2:
            # Set is won
            state["history"].append({"A": sA, "B": sB})
            if sA > sB: state["sets_A"] += 1
            else: state["sets_B"] += 1
            
            state["score_A"] = 0
            state["score_B"] = 0

            # Check match win condition
            if state["sets_A"] >= state["target_sets"] or state["sets_B"] >= state["target_sets"]:
                state["status"] = "finished"

        return state

    def is_finished(self, state: dict) -> bool:
        return state.get("status") == "finished"

    def get_winner(self, state: dict) -> int:
        if state["sets_A"] > state["sets_B"]: return 1
        elif state["sets_B"] > state["sets_A"]: return 2
        return 0

class VoliEngine(ScoringEngine):
    # Best of 3
    def get_default_state(self):
        return {
            "sets_A": 0,
            "sets_B": 0,
            "score_A": 0,
            "score_B": 0,
            "history": [],
            "status": "ongoing",
            "current_set": 1 # 1, 2, or 3
        }

    def process_action(self, state: dict, action: str, team: str) -> dict:
        if state["status"] == "finished": return state

        if action == "ADD_1":
            if team == "A": state["score_A"] += 1
            elif team == "B": state["score_B"] += 1
        elif action == "SUB_1":
            if team == "A": state["score_A"] = max(0, state["score_A"] - 1)
            elif team == "B": state["score_B"] = max(0, state["score_B"] - 1)

        # Determine target score based on current set
        target_score = 15 if state["current_set"] == 3 else 21
        
        sA = state["score_A"]
        sB = state["score_B"]

        # Check set win condition (target points, win by 2)
        if (sA >= target_score or sB >= target_score) and abs(sA - sB) >= 2:
            # Set is won
            state["history"].append({"A": sA, "B": sB})
            if sA > sB: state["sets_A"] += 1
            else: state["sets_B"] += 1
            
            state["score_A"] = 0
            state["score_B"] = 0
            state["current_set"] += 1

            # Check match win condition
            if state["sets_A"] >= 2 or state["sets_B"] >= 2:
                state["status"] = "finished"

        return state

    def is_finished(self, state: dict) -> bool:
        return state.get("status") == "finished"

    def get_winner(self, state: dict) -> int:
        if state["sets_A"] > state["sets_B"]: return 1
        elif state["sets_B"] > state["sets_A"]: return 2
        return 0

def get_engine_for_cabang(cabang_lomba: str) -> ScoringEngine:
    c = cabang_lomba.lower()
    if "basket" in c:
        return Basket3x3Engine()
    elif "tenis" in c:
        return TenisMejaEngine()
    elif "volly" in c or "voli" in c:
        return VoliEngine()
    
    # Default fallback
    return Basket3x3Engine()
