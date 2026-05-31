"""
Warm-up and cool-down exercise generation service
"""
from typing import List, Dict
from fastapiserver.models.workout_plan import Exercise


class WarmupCooldownService:
    """Service for generating warm-up and cool-down exercises."""
    
    # Standard warm-up exercises (dynamic stretches)
    WARMUP_EXERCISES = [
        {
            "name": "Arm Circles",
            "duration_seconds": 30,
            "instructions": ["Stand with feet shoulder-width apart", "Extend arms to sides", "Make small circles, gradually increasing size", "Reverse direction halfway through"]
        },
        {
            "name": "Leg Swings",
            "duration_seconds": 30,
            "instructions": ["Hold onto a wall for balance", "Swing one leg forward and back", "Keep leg straight", "Switch legs"]
        },
        {
            "name": "Hip Circles",
            "duration_seconds": 30,
            "instructions": ["Stand with hands on hips", "Make large circles with hips", "Reverse direction halfway through"]
        },
        {
            "name": "Torso Twists",
            "duration_seconds": 30,
            "instructions": ["Stand with feet shoulder-width apart", "Twist torso left and right", "Keep hips facing forward", "Let arms swing naturally"]
        },
        {
            "name": "High Knees",
            "duration_seconds": 30,
            "instructions": ["Stand tall", "Lift knees to hip height alternately", "Pump arms as you go", "Maintain quick pace"]
        },
        {
            "name": "Butt Kicks",
            "duration_seconds": 30,
            "instructions": ["Stand tall", "Kick heels up toward glutes", "Alternate legs quickly", "Keep core engaged"]
        },
        {
            "name": "Inchworms",
            "reps": 5,
            "instructions": ["Stand with feet hip-width apart", "Bend forward and place hands on ground", "Walk hands forward to plank position", "Walk feet toward hands", "Stand up and repeat"]
        },
        {
            "name": "Jumping Jacks",
            "duration_seconds": 30,
            "instructions": ["Start with feet together, arms at sides", "Jump feet apart while raising arms overhead", "Jump back to starting position", "Maintain steady rhythm"]
        }
    ]
    
    # Standard cool-down exercises (static stretches)
    COOLDOWN_EXERCISES = [
        {
            "name": "Hamstring Stretch",
            "duration_seconds": 30,
            "instructions": ["Sit on floor with one leg extended", "Reach toward toes of extended leg", "Hold stretch without bouncing", "Switch legs"]
        },
        {
            "name": "Quad Stretch",
            "duration_seconds": 30,
            "instructions": ["Stand on one leg", "Pull other foot toward glutes", "Keep knees together", "Hold for balance", "Switch legs"]
        },
        {
            "name": "Chest Stretch",
            "duration_seconds": 30,
            "instructions": ["Stand in doorway", "Place forearm on door frame", "Step forward until stretch felt in chest", "Hold position", "Switch arms"]
        },
        {
            "name": "Shoulder Stretch",
            "duration_seconds": 30,
            "instructions": ["Pull one arm across body", "Use other arm to pull gently", "Keep shoulders down", "Switch arms"]
        },
        {
            "name": "Triceps Stretch",
            "duration_seconds": 30,
            "instructions": ["Raise one arm overhead", "Bend elbow, reaching down back", "Use other hand to gently push elbow", "Switch arms"]
        },
        {
            "name": "Hip Flexor Stretch",
            "duration_seconds": 30,
            "instructions": ["Kneel on one knee", "Push hips forward", "Keep back straight", "Feel stretch in front of hip", "Switch legs"]
        },
        {
            "name": "Calf Stretch",
            "duration_seconds": 30,
            "instructions": ["Stand facing wall", "Step one foot back", "Keep back leg straight, heel down", "Lean into wall", "Switch legs"]
        },
        {
            "name": "Child's Pose",
            "duration_seconds": 45,
            "instructions": ["Kneel on floor", "Sit back on heels", "Extend arms forward on ground", "Rest forehead on floor", "Breathe deeply"]
        }
    ]
    
    def generate_warmup(self, focus: str, duration_minutes: int = 5) -> List[Exercise]:
        """
        Generate warm-up exercises based on workout focus.
        
        Args:
            focus: Workout focus (e.g., "Upper Body", "Lower Body", "Full Body")
            duration_minutes: Target duration in minutes
            
        Returns:
            List of warm-up exercises
        """
        # Select exercises based on focus
        if "upper" in focus.lower():
            selected = ["Arm Circles", "Torso Twists", "Inchworms", "Jumping Jacks"]
        elif "lower" in focus.lower() or "leg" in focus.lower():
            selected = ["Leg Swings", "Hip Circles", "High Knees", "Butt Kicks"]
        else:  # Full body or other
            selected = ["Arm Circles", "Leg Swings", "High Knees", "Inchworms"]
        
        exercises = []
        for name in selected:
            warmup_ex = next((ex for ex in self.WARMUP_EXERCISES if ex["name"] == name), None)
            if warmup_ex:
                exercise = Exercise(
                    exercise_id=f"warmup_{name.lower().replace(' ', '_')}",
                    name=warmup_ex["name"],
                    target_muscles=["dynamic_warmup"],
                    sets=1,
                    reps=f"{warmup_ex.get('duration_seconds', 30)}s" if "duration_seconds" in warmup_ex else str(warmup_ex.get('reps', 10)),
                    rest_seconds=30,  # Minimum rest between warm-up exercises
                    gif_url="",
                    instructions=warmup_ex["instructions"],
                    notes="Perform at moderate intensity to increase heart rate and blood flow"
                )
                exercises.append(exercise)
        
        return exercises
    
    def generate_cooldown(self, focus: str, duration_minutes: int = 5) -> List[Exercise]:
        """
        Generate cool-down exercises based on workout focus.
        
        Args:
            focus: Workout focus (e.g., "Upper Body", "Lower Body", "Full Body")
            duration_minutes: Target duration in minutes
            
        Returns:
            List of cool-down exercises
        """
        # Select exercises based on focus
        if "upper" in focus.lower() or "push" in focus.lower() or "pull" in focus.lower():
            selected = ["Chest Stretch", "Shoulder Stretch", "Triceps Stretch", "Child's Pose"]
        elif "lower" in focus.lower() or "leg" in focus.lower():
            selected = ["Hamstring Stretch", "Quad Stretch", "Hip Flexor Stretch", "Calf Stretch"]
        else:  # Full body or other
            selected = ["Hamstring Stretch", "Chest Stretch", "Hip Flexor Stretch", "Child's Pose"]
        
        exercises = []
        for name in selected:
            cooldown_ex = next((ex for ex in self.COOLDOWN_EXERCISES if ex["name"] == name), None)
            if cooldown_ex:
                exercise = Exercise(
                    exercise_id=f"cooldown_{name.lower().replace(' ', '_')}",
                    name=cooldown_ex["name"],
                    target_muscles=["static_stretch"],
                    sets=1,
                    reps=f"{cooldown_ex['duration_seconds']}s",
                    rest_seconds=30,  # Minimum rest between cool-down stretches
                    gif_url="",
                    instructions=cooldown_ex["instructions"],
                    notes="Hold each stretch without bouncing. Breathe deeply and relax into the stretch."
                )
                exercises.append(exercise)
        
        return exercises

# Made with Bob