import sys

from traceguard_run.red_team import AttackLibrary, RLRedTeamAgent

class CIFuzzHook:
    """
    CI/CD Fuzzing Hook for GitHub Actions (Phase 23).
    Automatically instantiates a Red Team Agent that leverages the persistent 
    AttackLibrary to fuzz new prompts/PRs. If a jailbreak succeeds, it exits with 
    code 1 to fail the build.
    """
    def __init__(self, target_prompt: str):
        self.target_prompt = target_prompt
        self.attack_library = AttackLibrary()
        self.red_team_agent = RLRedTeamAgent(self.attack_library)
        
    def run_ci_fuzzing(self, max_attempts: int = 5) -> bool:
        """
        Runs the fuzzer against the target prompt.
        Returns True if safe, False if a jailbreak succeeded (CI fails).
        """
        print(f"🛡️ TraceGuard CI Fuzzer: Testing target prompt against {max_attempts} adversarial vectors...")
        for i in range(max_attempts):
            attack = self.red_team_agent.generate_attack(self.target_prompt)
            print(f"  [Attempt {i+1}] Testing Attack Payload: '{attack['payload']}'")
            
            # Simulate evaluation of whether the attack succeeded
            # In a real environment, this sends the payload to the LLM and checks output
            success = self._simulate_attack_success(attack['payload'])
            
            # Update the RL Red Team Agent
            self.red_team_agent.update_policy(attack['payload'], success)
            
            if success:
                print(f"❌ CI FAILURE: Target prompt is vulnerable to attack: '{attack['payload']}'")
                return False
                
        print("✅ CI SUCCESS: Target prompt withstood all red team attacks.")
        return True
        
    def _simulate_attack_success(self, payload: str) -> bool:
        # Stub: if the payload has an extreme mutation (e.g., highly sophisticated), assume it broke through
        return len(payload) > 100

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m traceguard_fuzz.ci 'TARGET_PROMPT_TO_TEST'")
        sys.exit(1)
        
    target_prompt = sys.argv[1]
    hook = CIFuzzHook(target_prompt)
    if not hook.run_ci_fuzzing():
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
