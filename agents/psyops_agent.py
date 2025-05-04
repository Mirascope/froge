# Create an agent using mirasope to read GuessPrompt match history to learn more to defeat the opponent.

import os

from mirascope import BaseDynamicConfig, llm, prompt_template

# Example match history:
match_history_ex = {
    "total_scores": {"will_mira": 128, "you": 82},
    "matches": [
        {
            "image_url": "https://mnqkeyubddpfcpsigutk.supabase.co/storage/v1/object/public/images/match-images/1746311670.270363.webp",
            "your_prompt": "An alien hiking in Palm Springs with his pet human",
            "opponent_guess": "an alien backpacking in joshua tree with its dog",
            "similarity": 70.43,
            "timestamp": "15 minutes ago",
        },
        {
            "image_url": "https://mnqkeyubddpfcpsigutk.supabase.co/storage/v1/object/public/images/match-images/1746311866.411077.webp",
            "opponent_prompt": "an alien backpacking in joshua tree with its dog",
            "your_guess": "An alien backpacking with his dog in JTree",
            "similarity": 89.44,
            "timestamp": "12 minutes ago",
        },
        {
            "image_url": "https://mnqkeyubddpfcpsigutk.supabase.co/storage/v1/object/public/images/match-images/1746312024.865616.webp",
            "your_prompt": "An alien backpacking with his dog in JTree",
            "opponent_guess": "alien hiking with their dog in palm springs",
            "similarity": 57.15,
            "timestamp": "11 minutes ago",
        },
        # Additional entries can be appended here
    ],
}


def match_history_to_string(history):
    lines = []
    scores = history.get("total_scores", {})
    lines.append(
        f"Total Scores — You: {scores.get('you', 0)}, Opponent: {scores.get('will_mira', 0)}\n"
    )

    for i, match in enumerate(history.get("matches", []), 1):
        lines.append(f"Match {i} ({match.get('timestamp', 'unknown time')}):")
        if "your_prompt" in match:
            lines.append(f"  Your prompt: {match['your_prompt']}")
            lines.append(f"  Opponent's guess: {match['opponent_guess']}")
        else:
            lines.append(f"  Opponent's prompt: {match['opponent_prompt']}")
            lines.append(f"  Your guess: {match['your_guess']}")
        lines.append(f"  Similarity: {match['similarity']}%\n")

    return "\n".join(lines)


# prompt_context = match_history_to_string(match_history_ex)
# print(prompt_context)


@llm.call(provider="openai", model="gpt-4o-mini")
@prompt_template(
    """
    SYSTEM:
    You are an intelligent agent that reads "Prompt Tennis" match history to create strategic insight into 
    an opponent's mindset and strategy to improve another agent's ability to beat them in subsequent match guesses.

    Output short LLM-readable string with specific tactics and strategy the AI competitor agent can use to improve subsequent guesses.
    
    Explanation of the "Prompt Tennis" game:
    You play against a human opponent.
    The game starts with a challenge: guess the prompt used to generate an image.
    If your guess has a cosine similarity of 0.85 or higher with the original prompt, you win.
    Otherwise, your guess is used to generate a new challenge image for your opponent.
    The game is played in turns until one of you wins.

    USER:
    Here is the match history:
    {formatted_match_history}
    """
)
def assess_opponents_psyche(match_history_ex: dict) -> BaseDynamicConfig:
    return {
        "computed_fields": {
            "formatted_match_history": match_history_to_string(match_history_ex)
        }
    }


response: llm.CallResponse = assess_opponents_psyche(match_history_ex)
print(response.content)

"""
Example output:

To enhance your guessing strategy, focus on identifying key synonyms and contextual elements 
from previous prompts. Your opponent tends to mix location and action while maintaining a similar
subject. Consider using varied synonyms for the elements in their prompts. For example, instead 
of "hiking," use "trekking" or "exploring," and instead of "alien," try "extraterrestrial." This 
strategy will increase your chances of attaining a higher cosine similarity in your future guesses.
"""
