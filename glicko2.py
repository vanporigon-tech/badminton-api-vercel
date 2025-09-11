import math
from typing import Tuple, List

class Glicko2:
    """Implementation of Glicko-2 rating system"""
    
    def __init__(self, tau: float = 0.5):
        self.tau = tau  # System constant
    
    def calculate_new_rating(self, rating: float, rd: float, volatility: float, 
                           opponent_ratings: List[float], opponent_rds: List[float], 
                           scores: List[float]) -> Tuple[float, float, float]:
        """
        Calculate new rating, RD, and volatility using Glicko-2
        
        Args:
            rating: Current rating
            rd: Current rating deviation
            volatility: Current volatility
            opponent_ratings: List of opponent ratings
            opponent_rds: List of opponent RDs
            scores: List of scores (1 for win, 0 for loss, 0.5 for draw)
        
        Returns:
            Tuple of (new_rating, new_rd, new_volatility)
        """
        if not opponent_ratings:
            return rating, rd, volatility
        
        # Step 1: Convert rating and RD to Glicko-2 scale
        mu = (rating - 1500) / 173.7178
        phi = rd / 173.7178
        
        # Step 2: Compute the value of the volatility
        volatility = self._compute_volatility(mu, phi, volatility, opponent_ratings, opponent_rds, scores)
        
        # Step 3: Update the rating deviation to the pre-rating period value
        phi_star = math.sqrt(phi * phi + volatility * volatility)
        
        # Step 4: Update the rating and RD
        new_mu, new_phi = self._update_rating(mu, phi_star, opponent_ratings, opponent_rds, scores)
        
        # Step 5: Convert back to Glicko scale
        new_rating = 173.7178 * new_mu + 1500
        new_rd = 173.7178 * new_phi
        
        return new_rating, new_rd, volatility
    
    def _compute_volatility(self, mu: float, phi: float, sigma: float, 
                           opponent_ratings: List[float], opponent_rds: List[float], 
                           scores: List[float]) -> float:
        """Compute new volatility using iterative algorithm"""
        # Convert opponent ratings to Glicko-2 scale
        opponent_mus = [(r - 1500) / 173.7178 for r in opponent_ratings]
        opponent_phis = [rd / 173.7178 for rd in opponent_rds]
        
        # Compute g(phi) for each opponent
        g_phis = [1 / math.sqrt(1 + 3 * phi * phi / (math.pi * math.pi)) for phi in opponent_phis]
        
        # Compute E(mu, mu_j, phi_j) for each opponent
        expectations = []
        for i, (opp_mu, g_phi) in enumerate(zip(opponent_mus, g_phis)):
            e = 1 / (1 + math.exp(-g_phi * (mu - opp_mu)))
            expectations.append(e)
        
        # Compute v (variance)
        v = 0.0
        for g_phi, expectation in zip(g_phis, expectations):
            v += g_phi * g_phi * expectation * (1 - expectation)
        # Guard against degenerate cases where expectation is 0 or 1 exactly for all opponents
        if v <= 0.0:
            v = 1e-9
        v = 1.0 / v
        
        # Compute delta
        delta = 0
        for i, (g_phi, expectation, score) in enumerate(zip(g_phis, expectations, scores)):
            delta += g_phi * (score - expectation)
        delta = v * delta
        
        # Iterative algorithm for volatility
        a = math.log(sigma * sigma)
        tau = self.tau
        A = a
        # Инициализация B по рекомендациям Glicko-2: если условие не выполняется, подбираем B так, чтобы f(B) < 0
        if delta * delta > phi * phi + v:
            B = math.log(delta * delta - phi * phi - v)
        else:
            B = a - 1.0
            f_b_test = self._f(B, delta, phi, v, tau)
            # Двигаемся вниз, пока не станет < 0, чтобы избежать деления на (f_b - f_a) == 0
            step = 1.0
            guard_iter = 0
            while f_b_test >= 0 and guard_iter < 50:
                B -= step
                f_b_test = self._f(B, delta, phi, v, tau)
                guard_iter += 1
        
        f_a = self._f(A, delta, phi, v, tau)
        f_b = self._f(B, delta, phi, v, tau)
        
        while abs(B - A) > 0.000001:
            denom = (f_b - f_a)
            if abs(denom) < 1e-12:
                # Избегаем деления на ноль — небольшой сдвиг
                denom = 1e-12 if denom >= 0 else -1e-12
            C = A + (A - B) * f_a / denom
            f_c = self._f(C, delta, phi, v, tau)
            
            if f_c * f_b < 0:
                A = B
                f_a = f_b
            else:
                f_a = f_a / 2
            
            B = C
            f_b = f_c
        
        return math.exp(A / 2)
    
    def _f(self, x: float, delta: float, phi: float, v: float, tau: float) -> float:
        """Helper function for volatility computation"""
        ex = math.exp(x)
        return (ex * (delta * delta - phi * phi - v - ex)) / (2 * (phi * phi + v + ex) * (phi * phi + v + ex)) - (x - math.log(tau * tau)) / (tau * tau)
    
    def _update_rating(self, mu: float, phi: float, opponent_ratings: List[float], 
                      opponent_rds: List[float], scores: List[float]) -> Tuple[float, float]:
        """Update rating and RD"""
        # Convert opponent ratings to Glicko-2 scale
        opponent_mus = [(r - 1500) / 173.7178 for r in opponent_ratings]
        opponent_phis = [rd / 173.7178 for rd in opponent_rds]
        
        # Compute g(phi) for each opponent
        g_phis = [1 / math.sqrt(1 + 3 * phi * phi / (math.pi * math.pi)) for phi in opponent_phis]
        
        # Compute E(mu, mu_j, phi_j) for each opponent
        expectations = []
        for i, (opp_mu, g_phi) in enumerate(zip(opponent_mus, g_phis)):
            e = 1 / (1 + math.exp(-g_phi * (mu - opp_mu)))
            expectations.append(e)
        
        # Compute v (variance)
        v = 0
        for g_phi, expectation in zip(g_phis, expectations):
            v += g_phi * g_phi * expectation * (1 - expectation)
        v = 1 / v
        
        # Compute delta
        delta = 0
        for i, (g_phi, expectation, score) in enumerate(zip(g_phis, expectations, scores)):
            delta += g_phi * (score - expectation)
        delta = v * delta
        
        # Update mu and phi (with guards for stability)
        new_mu = mu + v * delta
        denom = (phi * phi)
        if denom <= 0.0:
            denom = 1e-9
        inv = 1.0 / denom + 1.0 / max(v, 1e-9)
        new_phi = 1.0 / math.sqrt(inv)
        
        return new_mu, new_phi

# Global instance
glicko2 = Glicko2()

def calculate_team_rating(players: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    """
    Calculate virtual team rating from individual players
    
    Args:
        players: List of tuples (rating, rd, volatility) for each player
    
    Returns:
        Tuple of (team_rating, team_rd, team_volatility)
    """
    if not players:
        return 1500.0, 350.0, 0.06
    
    # Average rating
    team_rating = sum(p[0] for p in players) / len(players)
    
    # Maximum RD (most uncertain player)
    team_rd = max(p[1] for p in players)
    
    # Maximum volatility
    team_volatility = max(p[2] for p in players)
    
    return team_rating, team_rd, team_volatility

def distribute_rating_changes(players: List[Tuple[float, float, float]], 
                            team_rating_change: float, team_rd_change: float, 
                            team_volatility_change: float) -> List[Tuple[float, float, float]]:
    """
    Distribute team rating changes back to individual players
    
    Args:
        players: List of tuples (rating, rd, volatility) for each player
        team_rating_change: Change in team rating
        team_rd_change: Change in team RD
        team_volatility_change: Change in team volatility
    
    Returns:
        List of new (rating, rd, volatility) for each player
    """
    if not players:
        return []
    
    # Distribute changes equally among players
    rating_change_per_player = team_rating_change / len(players)
    rd_change_per_player = team_rd_change / len(players)
    volatility_change_per_player = team_volatility_change / len(players)
    
    new_players = []
    for rating, rd, volatility in players:
        new_rating = rating + rating_change_per_player
        new_rd = rd + rd_change_per_player
        new_volatility = volatility + volatility_change_per_player
        
        # Ensure RD stays within reasonable bounds
        new_rd = max(30.0, min(350.0, new_rd))
        
        new_players.append((new_rating, new_rd, new_volatility))
    
    return new_players

