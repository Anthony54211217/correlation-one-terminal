import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

        global BREAKPOINT
        BREAKPOINT = 'BREAKPOINT'
        self.base = (
            # First turrets
            (TURRET, [3, 12]),
            (TURRET, [7, 12]),
            (TURRET, [9, 12]),
            (TURRET, [26, 12]),

            # First front walls
            (WALL, [11, 13]),
            (WALL, [10, 13]),
            (WALL, [9, 13]),
            (WALL, [8, 13]),
            (WALL, [7, 13]),
            (WALL, [6, 13]),
            (WALL, [5, 13]),
            (WALL, [4, 13]),
            (WALL, [3, 13]),
            (WALL, [2, 13]),
            (WALL, [1, 13]),
            (WALL, [0, 13]),
            (WALL, [25, 13]),
            (WALL, [26, 13]),
            (WALL, [27, 13]),

            # Back walls
            (WALL, [24, 12]),
            (WALL, [23, 11]),
            (WALL, [22, 10]),
            (WALL, [21, 9]),
            (WALL, [20, 8]),
            (WALL, [19, 7]),
            (WALL, [18, 7]),
            (WALL, [17, 7]),
            (WALL, [16, 7]),
            (WALL, [15, 7]),
            (WALL, [14, 7]),
            (WALL, [13, 7]),
            (WALL, [12, 7]),
            (WALL, [11, 7]),
            (WALL, [10, 8]),
            (WALL, [9, 9]),
            (WALL, [8, 10]),

            # Second turrets
            (BREAKPOINT, 6),
            (TURRET, [7, 8]),
            (BREAKPOINT, 6),
            (TURRET, [5, 10]),
            (BREAKPOINT, 6),
            (TURRET, [5, 12]),

            # First supports and side walls
            (SUPPORT, [4, 11]),
            (WALL, [5, 9]),
            (WALL, [22, 9]),
            (WALL, [19, 6]),

            # Second supports
            (SUPPORT, [6, 9]),
            (SUPPORT, [8, 7]),
            (SUPPORT, [9, 6]),

            # Third turrets
            (BREAKPOINT, 6),
            (TURRET, [1, 12]),

            # First front wall upgrades
            (None, [11, 13]),
            (None, [10, 13]),
            (None, [9, 13]),
            (None, [8, 13]),
            (None, [7, 13]),
            (None, [6, 13]),
            (None, [5, 13]),
            (None, [4, 13]),
            (None, [3, 13]),
            (None, [2, 13]),
            (None, [1, 13]),
            (None, [0, 13]),
            (None, [25, 13]),
            (None, [26, 13]),
            (None, [27, 13]),

            # Fourth turrets, second front walls and upgrades, and third supports
            (BREAKPOINT, 7),
            (TURRET, [11, 12]),
            (WALL, [12, 13]),
            (WALL, [13, 13]),
            (SUPPORT, [10, 5]),
            (SUPPORT, [11, 5]),
            (SUPPORT, [12, 5]),
            (None, [12, 13]),
            (None, [13, 13]),

            # Fifth turrets, third front walls and upgrades, and fourth supports
            (BREAKPOINT, 7),
            (TURRET, [13, 12]),
            (WALL, [14, 13]),
            (WALL, [15, 13]),
            (SUPPORT, [13, 5]),
            (SUPPORT, [14, 5]),
            (SUPPORT, [15, 5]),
            (None, [14, 13]),
            (None, [15, 13]),

            # Fifth supports
            (SUPPORT, [16, 5]),
            (SUPPORT, [17, 5]),

            # Fifth supports
            (SUPPORT, [11, 4]),
            (SUPPORT, [12, 4]),
            (SUPPORT, [13, 4]),
            (SUPPORT, [14, 4]),
            (SUPPORT, [15, 4]),
            (SUPPORT, [16, 4]),

            # Sixth supports
            (SUPPORT, [12, 3]),
            (SUPPORT, [13, 3]),
            (SUPPORT, [14, 3]),
            (SUPPORT, [15, 3]),

            # Seventh supports
            (SUPPORT, [13, 2]),
            (SUPPORT, [14, 2]),
        )
        self.rebuild_thresholds = {
            WALL: 0.75,
            TURRET: 0.5,
        }
        self.interceptor_spawn_locations = [4, 9], [23, 9], [19, 5], [20, 6]
        self.interceptor_spawn_count = 1
        self.interceptor_mp_threshold = 10
        self.scout_spawn_location = [5, 8]
        self.scout_spawn_count = 5
        self.demolisher_spawn_location = [7, 6]
        self.demolisher_spawn_count = 1000
        self.scout_and_demolisher_mp_threshold = 11

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        self.defend(game_state)
        self.attack(game_state)

        # # Now build reactive defenses based on where the enemy scored
        # self.build_reactive_defense(game_state)

        # # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        # if game_state.turn_number < 5:
        #     self.stall_with_interceptors(game_state)
        # else:
        #     # Now let's analyze the enemy base to see where their defenses are concentrated.
        #     # If they have many units in the front we can build a line for our demolishers to attack them at long range.
        #     if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
        #         self.demolisher_line_strategy(game_state)
        #     else:
        #         # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

        #         # Only spawn Scouts every other turn
        #         # Sending more at once is better since attacks can only hit a single scout at a time
        #         if game_state.turn_number % 2 == 1:
        #             # To simplify we will just check sending them from back left and right
        #             scout_spawn_location_options = [[13, 0], [14, 0]]
        #             best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
        #             game_state.attempt_spawn(SCOUT, best_location, 1000)

        #         # Lastly, if we have spare SP, let's build some supports
        #         support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
        #         game_state.attempt_spawn(SUPPORT, support_locations)

    def defend(self, game_state):
        for shorthand, location in self.base:
            if shorthand != BREAKPOINT \
                    and shorthand in self.rebuild_thresholds \
                    and game_state.contains_stationary_unit(location):
                threshold = self.rebuild_thresholds[shorthand]

                for unit in game_state.game_map[location]:
                    if not unit.player_index and unit.unit_type == shorthand \
                            and unit.health < threshold * unit.max_health:
                        game_state.attempt_remove(location)

        for shorthand, location in self.base:
            if shorthand is None:
                game_state.attempt_upgrade(location)
            elif shorthand == BREAKPOINT:
                if game_state.get_resource(SP) < location:
                    break
            else:
                game_state.attempt_spawn(shorthand, location)

    def attack(self, game_state):
        if game_state.get_resource(MP, 1) >= self.interceptor_mp_threshold:
            game_state.attempt_spawn(
                INTERCEPTOR,
                self.interceptor_spawn_locations,
                self.interceptor_spawn_count,
            )

        if game_state.get_resource(MP) \
                >= self.scout_and_demolisher_mp_threshold:
            gamelib.debug_write('attempting Desu!')
            gamelib.debug_write(
            game_state.attempt_spawn(
                SCOUT,
                self.scout_spawn_location,
                self.scout_spawn_count,
            )
            )
            gamelib.debug_write(
            game_state.attempt_spawn(
                DEMOLISHER,
                self.demolisher_spawn_location,
                self.demolisher_spawn_count,
            )
            )

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
