import math

class ScoringService:
    @staticmethod
    def calculate_points(challenge, solve_count=None):
        if solve_count is None:
            solve_count = challenge.solve_count
            
        initial = challenge.initial_points
        minimum = challenge.minimum_points
        decay_type = (challenge.decay_type or "static").lower()
        decay_rate = challenge.decay_rate
        
        if decay_type == "static" or solve_count <= 0:
            return initial
            
        if decay_type == "linear":
            if decay_rate <= 0:
                return initial
            points = initial - (solve_count * decay_rate)
            return max(minimum, points)
            
        if decay_type == "logarithmic":
            if decay_rate <= 1:
                return initial
            if solve_count <= 1:
                return initial
            val = initial - (initial - minimum) * (math.log(solve_count) / math.log(decay_rate))
            return max(minimum, int(math.ceil(val)))
            
        # Custom placeholder framework
        return initial
