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
        # gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        # gamelib.debug_write('Configuring your custom algo strategy...')
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
        self.death_info = []
        self.self_destruct_info = []
        # self.scored_on_locations = []
        self.avg_sum = 0
        self.avg_count = 0
        self.avg = 10
        self.opponent_spawn_locations = []
        self.most_common = {}
        self.opponent_left_x = [i for i in range(0, 14)]
        self.opponent_right_x = [i for i in range(13, 28)]
        # list to store structures that were removed in the previous round that need to be rebuilt
        self.to_rebuild = []
        # all possible spawn locations for mobile units
        self.spawn_locaations = [[0, 13], [27, 13], [1, 12], [26, 12], [2, 11], [25, 11], [3, 10], [24, 10], [4, 9], [23, 9], [5, 8], [22, 8], [6, 7], [21, 7], [7, 6], [20, 6], [8, 5], [19, 5], [9, 4], [18, 4], [10, 3], [17, 3], [11, 2], [16, 2], [12, 1], [15, 1], [13, 0], [14, 0]]
        # list of structures/upgrades to build: will do so in order, so, put higher priority structures in front of list, left-handed
        self.base_l = [([3, 12], TURRET), 
                       ([5, 11], TURRET), 
                       ([7, 10], TURRET), 
                       ([0, 13], WALL), 
                       ([2, 13], WALL),
                       ([3, 13], WALL), 
                       ([4, 13], WALL), 
                       ([27, 13], WALL),
                       ([26, 13], WALL), 
                       ([25, 13], WALL), 
                       ([24, 12], WALL), 
                       ([5, 12], WALL),
                       ([7, 12], WALL), 
                       ([7, 11], WALL), 
                       ([8, 10], WALL), 
                       ([25, 11], WALL), 
                       ([24, 10], WALL), 
                       ([8, 9], WALL), 
                       ([9, 8], WALL), 
                       ([23, 9], WALL),
                       ([22, 8], WALL), 
                       ([10, 7], WALL), 
                       ([11, 7], WALL), 
                       ([12, 7], WALL), 
                       ([13, 7], WALL),
                       ([14, 7], WALL), 
                       ([15, 7], WALL), 
                       ([16, 7], WALL), 
                       ([17, 7], WALL), 
                       ([18, 7], WALL),
                       ([19, 7], WALL), 
                       ([20, 7], WALL), 
                       ([21, 7], WALL), 
                       ([0, 13], "UPGRADE_WALL"), 
                       ([2, 13], "UPGRADE_WALL"), 
                       ([3, 13], "UPGRADE_WALL"), 
                       ([4, 13], "UPGRADE_WALL"),
                       ([27, 13], "UPGRADE_WALL"), 
                       ([26, 13], "UPGRADE_WALL"),
                       ([25, 13], "UPGRADE_WALL"), 
                       ([24, 12], "UPGRADE_WALL"),
                       ([5, 12], "UPGRADE_WALL"), 
                       ([7, 12], "UPGRADE_WALL"),
                       ([7, 11], "UPGRADE_WALL"), 
                       ([8, 10], "UPGRADE_WALL"),
                       ([25, 12], TURRET), 
                       ([4, 12], TURRET),
                       ([26, 12], TURRET), 
                       ([11, 6], SUPPORT), 
                       ([12, 6], SUPPORT), 
                       ([10, 6], SUPPORT), 
                       ([11, 5], SUPPORT), 
                       ([3, 12], "UPGRADE_TURRET"), 
                       ([25, 12], "UPGRADE_TURRET"),
                       ([7, 10], "UPGRADE_TURRET"), 
                       ([5, 11], "UPGRADE_TURRET"), 
                       ([4, 11], SUPPORT), ([4, 11], "UPGRADE_SUPPORT"), 
                       ([7, 9], SUPPORT),([7, 9], "UPGRADE_SUPPORT"), 
                       ([8, 8], SUPPORT), ([8, 8], "UPGRADE_SUPPORT"),
                       ([4, 12], "UPGRADE_TURRET"), 
                       ([26, 12], "UPGRADE_TURRET"), 
                       ([7, 8], SUPPORT),([7, 8], "UPGRADE_SUPPORT"), 
                       ([9, 7], SUPPORT), 
                       ([8, 7], SUPPORT), 
                       ([9, 6], SUPPORT),
                       ([5, 10], SUPPORT), ([5, 10], "UPGRADE_SUPPORT")
        ]
        # corner wall that will be continuously built and rebuilt, left-handed
        self.corner_walls_l = [[1, 13]]
        # potential additional walls to extend mobile unit path to avoid self-destructing interceptors
        self.avoid_interceptor_walls_l = [[14, 1], 
                                          [14, 3], 
                                          [13, 3], 
                                          [12, 2], 
                                          [15, 3], 
                                          [16, 4], 
                                          [17, 5], 
                                          [11, 4], 
                                          [12, 5], 
                                          [13, 5], 
                                          [14, 5], 
                                          [15, 6]
        ]
        # potential walls to trap in an interceptor to self-destruct
        self.interceptor_trap_short_l = [[3, 11], [2, 12]]
        # interceptor self-destruct trap spawn location, for a short (4 frames) "fuse"
        self.interceptor_trap_spawn_short_l = [2, 11]
        # potential walls to trap in an interceptor to self-destruct
        self.interceptor_trap_long_l = [[4, 10], [2, 12]]
        # interceptor self-destruct trap spawn location, for a long (8 frames) "fuse"
        self.interceptor_trap_spawn_long_l = [3, 10]
        # x-coordinates of area of opponent's area to calculate their "defensive score"
        self.count_enemy_unit_x_l = [0, 1, 2, 3, 4, 5]
        # y-coordinates of area of opponent's area to calculate their "defensive score"
        self.count_enemy_unit_y_l = [14, 15, 16, 17, 18, 19]

        self.demolisher_spawn_l = [13, 0]
        self.scout_spawn_l = [14, 0]
        self.attack_wall_l = [6, 11]

        # the follow "base" is the same layout but reflected on the y-axis
        self.base_r = []
        for location, structure in self.base_l:
            self.base_r.append(([27 - location[0], location[1]], structure))
        # corner wall that will be continously built and rebuilt, right-handed
        self.corner_walls_r = [[26, 13]]
        # potential additional walls to extend mobile unit path to avoid self-destructing interceptors
        self.avoid_interceptor_walls_r = [[13, 1], 
                                          [13, 3], 
                                          [14, 3], 
                                          [15, 2], 
                                          [12, 3], 
                                          [11, 4], 
                                          [10, 5], 
                                          [16, 4], 
                                          [15, 5], 
                                          [14, 5], 
                                          [13, 5], 
                                          [12, 6]
        ]
        # potential walls to trap in an interceptor to self-destruct
        self.interceptor_trap_short_r = [[24, 11], [25, 12]]
        # interceptor self-destruct trap spawn location
        self.interceptor_trap_spawn_short_r = [25, 11]
        # potential walls to trap in an interceptor to self-destruct
        self.interceptor_trap_long_r = [[23, 10], [25, 12]]
        # interceptor self-destruct trap spawn location, for a long (8 frames) "fuse"
        self.interceptor_trap_spawn_long_r = [24, 10]
        # boolean to decide if algo should add walls to extend path for our own mobile units
        self.avoid_interceptor_path = False
        # x-coordinates of area of opponent's area to calculate their "defensive score"
        self.count_enemy_unit_x_r = [27, 26, 25, 24, 23, 22]
        # y-coordinates of area of opponent's area to calculate their "defensive score"
        self.count_enemy_unit_y_r = [14, 15, 16, 17, 18, 19]
        # boolean to store whether base is left-handed or right-handed
        self.left = True

        self.demolisher_spawn_r = [14, 0]
        self.scout_spawn_r = [13, 0]
        self.attack_wall_r = [21, 11]

        self.enemy_left_half_x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        self.enemy_right_half_x = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        self.enemy_left_half_y = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        self.enemy_right_half_y = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

        # generate a random number to decide if base will be left or right-handed
        rand_side = random.randint(0, 1)
        if rand_side == 0:
            self.left = True
            self.base = self.base_l
            self.demolisher_spawn = self.demolisher_spawn_l
            self.scout_spawn = self.scout_spawn_l
            self.attack_wall = self.attack_wall_l
            self.count_enemy_unit_x = self.count_enemy_unit_x_l
            self.count_enemy_unit_y = self.count_enemy_unit_y_l
            self.avoid_interceptor_walls = self.avoid_interceptor_walls_l
            self.corner_walls = self.corner_walls_l
        else:
            self.left = False
            self.base = self.base_r
            self.demolisher_spawn = self.demolisher_spawn_r
            self.scout_spawn = self.scout_spawn_r
            self.attack_wall = self.attack_wall_r
            self.count_enemy_unit_x = self.count_enemy_unit_x_r
            self.count_enemy_unit_y = self.count_enemy_unit_y_r
            self.avoid_interceptor_walls = self.avoid_interceptor_walls_r
            self.corner_walls = self.corner_walls_r
        
        self.picked_side = False


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        # gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        # self.starter_strategy(game_state)
        self.strategy(game_state)
        game_state.submit_turn()

    def strategy(self, game_state):
        # if we haven't picked which side to build base yet
        if self.picked_side == False:
            # calculate the defence value of both halves of opponent play area
            left_val, right_val = self.calculate_defence_value_halves(game_state)

        # if opponent spawned an interceptor that destroyed our units
        for self_destruct_info in self.self_destruct_info:
            if game_state.turn_number - 1 == self_destruct_info[0]:
                if self_destruct_info[2]:
                    self.avoid_interceptor_path = True
                    
        # TODO: probably remove and and set to constant value of 9 ? -> help to beat against echaveman
        if self.avg_count != 0:
            self.avg = max(1, math.floor(self.avg_sum/self.avg_count))

        # finding the most common spawn location for our opponent, likely not useful 
        # if self.opponent_spawn_locations:
        #     most_common = {}
        #     for location in self.opponent_spawn_locations:
        #         if location not in most_common.keys():
        #             most_common[location] = 1
        #         else:
        #             most_common[location] += 1
        #     most_common_spawn_location = [max(most_common, key=most_common.get)[0], max(most_common, key=most_common.get)[1]]
        #     # game_state.attempt_spawn(SCOUT, [most_common_spawn_location[0], 27 - most_common_spawn_location[1]])
        #     # gamelib.debug_write(self.opponent_spawn_locations)
        #     # gamelib.debug_write("most common:", [most_common_spawn_location[0], 27 - most_common_spawn_location[1]])
        #     most_common_opponent_path = game_state.find_path_to_edge(start_location = most_common_spawn_location)
        #     gamelib.debug_write(most_common_opponent_path)

        # generate a random number to decide if a "short" or "long" fuse interceptor will be spawned
        # TODO: probably removing 
        rand_num = random.randint(0, 1)
        if rand_num == 0:
            # self.avoid_interceptor_path = False
            if (self.left):
                self.interceptor_trap = self.interceptor_trap_short_l
                self.interceptor_trap_spawn = self.interceptor_trap_spawn_short_l
            else:
                self.interceptor_trap = self.interceptor_trap_short_r
                self.interceptor_trap_spawn = self.interceptor_trap_spawn_short_r
        else:
            # self.avoid_interceptor_path = True, turning this off for now
            if (self.left):
                self.interceptor_trap = self.interceptor_trap_long_l
                self.interceptor_trap_spawn = self.interceptor_trap_spawn_long_l
            else:
                self.interceptor_trap = self.interceptor_trap_long_r
                self.interceptor_trap_spawn = self.interceptor_trap_spawn_long_r

        # if building were refunded previous round, rebuild them this round
        if self.to_rebuild:
            for unit_type, unit_location in self.to_rebuild:
                game_state.attempt_spawn(unit_type, unit_location)
                self.to_rebuild.remove((unit_type, unit_location))

        # find and remove all damaged building so they can be rebuilt
        self.remove_damaged(game_state) 

        # send interceptors on first 2 turns to build up SP to have full base built
        if game_state.turn_number <= 2:
            interceptor_locations = [[5, 8], [22, 8]]
            game_state.attempt_spawn(INTERCEPTOR, interceptor_locations)

        elif game_state.turn_number >= 3:
            # get information of player's SP & MP
            my_resources = game_state.get_resources(player_index = 0)
            opponent_resources = game_state.get_resources(player_index = 1)
            # picking which base layout, left-hand or right-hand depending on opponent base halves defence value
            if self.picked_side == False:
                if (left_val >= right_val):
                    self.left = True
                    self.base = self.base_l
                    self.demolisher_spawn = self.demolisher_spawn_l
                    self.scout_spawn = self.scout_spawn_l
                    self.attack_wall = self.attack_wall_l
                    self.count_enemy_unit_x = self.count_enemy_unit_x_l
                    self.count_enemy_unit_y = self.count_enemy_unit_y_l
                    self.avoid_interceptor_walls = self.avoid_interceptor_walls_l
                    self.corner_walls = self.corner_walls_l
                    self.picked_side = True
                elif right_val > left_val:
                    self.left = False
                    self.base = self.base_r
                    self.demolisher_spawn = self.demolisher_spawn_r
                    self.scout_spawn = self.scout_spawn_r
                    self.attack_wall = self.attack_wall_r
                    self.count_enemy_unit_x = self.count_enemy_unit_x_r
                    self.count_enemy_unit_y = self.count_enemy_unit_y_r
                    self.avoid_interceptor_walls = self.avoid_interceptor_walls_r
                    self.corner_walls = self.corner_walls_r
                    self.picked_side = True

            # detect number of turrets on small triangle on side we are attacking
            num_left_turrets = self.detect_enemy_unit(game_state, TURRET, self.count_enemy_unit_x, self.count_enemy_unit_y)
            num_left_upgraded_walls = self.detect_upgraded_enemy_unit(game_state, WALL, self.count_enemy_unit_x, self.count_enemy_unit_y)
            score_add = num_left_upgraded_walls//3
            if num_left_turrets == 0 and num_left_upgraded_walls != 0:
                num_demolishers = 3
                num_scout = math.floor(max(my_resources[1] - 9, 0))
            elif num_left_turrets == 0 and num_left_upgraded_walls == 0:
                num_demolishers = 0
                num_scout = math.floor(max(my_resources[1], 0))
            elif (num_left_turrets == 1 or num_left_turrets == 2) and num_left_upgraded_walls <= 2:
                num_demolishers = 3
                num_scout = math.floor(max(my_resources[1] - 9, 0))
            else:
                defensive_measure = num_left_turrets + score_add
                if opponent_resources[0] >= 6:
                    defensive_measure += 1
                if defensive_measure == 1:
                    num_demolishers = 4
                    num_scout = math.floor(max(my_resources[1] - 12, 0))
                elif defensive_measure == 2:
                    num_demolishers = 5
                    num_scout = math.floor(max(my_resources[1] - 15, 0))
                elif defensive_measure == 3 or defensive_measure == 4: 
                    num_demolishers = 6
                    num_scout = math.floor(max(my_resources[1] - 18, 0))
                #elif defensive_measure == 5:
                #   num_demolishers = 7
                #  num_scout = math.floor(max(my_resources[1] - 21, 0))
                else:
                    num_demolishers = 8
                    num_scout = math.floor(max(my_resources[1] - 24, 0))
            if game_state.turn_number >= 3:
                if my_resources[1] >= (num_demolishers*3 + num_scout):
                    # spawn demolishers
                    game_state.attempt_spawn(DEMOLISHER, self.demolisher_spawn, num_demolishers)
                    game_state.attempt_spawn(SCOUT, self.scout_spawn, num_scout)
                    game_state.attempt_spawn(WALL, self.attack_wall)
                    game_state.attempt_remove(self.attack_wall)
                    if self.avoid_interceptor_path:
                        game_state.attempt_spawn(WALL, self.avoid_interceptor_walls)
                else:
                    if game_state.turn_number >= 3:
                        # spawn corner walls
                        game_state.attempt_spawn(WALL, self.corner_walls)
                        # remove corner walls to allow us to attack corner if we choose to
                        game_state.attempt_remove(self.corner_walls)
                    # if opponent has a lot of MP (15), spawn an interceptor, put this here so that the demolishers will not be blocked 
                    if opponent_resources[1] >= self.avg:
                        # TODO: need logic to decide which side to spawn interceptor to self-destruct on
                        # game_state.attempt_spawn(INTERCEPTOR, [25, 11])
                        # spawn walls to trap interceptor so it will self destruct to defend
                        game_state.attempt_spawn(WALL, self.interceptor_trap)
                        game_state.attempt_remove(self.interceptor_trap)
                        game_state.attempt_spawn(INTERCEPTOR, self.interceptor_trap_spawn)

            for location, structure in self.base:
                # get information of player's SP & MP
                my_resources = game_state.get_resources(player_index = 0)
                opponent_resources = game_state.get_resources(player_index = 1)

                # if we don't have enough resources to spawn what is on the priority list, return and wait for more resources
                if structure == TURRET and my_resources[0] < 6:
                    return
                elif structure == "UPGRADE_WALL" and my_resources[0] < 1.5:
                    return
                elif structure == "UPGRADE_TURRET" and my_resources[0] < 6:
                    return
                elif structure == "UPGRADE_SUPPORT" and my_resources[0] < 2:
                    return
                if (structure != "UPGRADE_WALL") and (structure != "UPGRADE_SUPPORT") and (structure != "UPGRADE_TURRET"):
                    game_state.attempt_spawn(structure, location)
                else:
                    game_state.attempt_upgrade(location)

    def calculate_defence_value_halves(self, game_state):
        left_val = 0
        valid_x = self.enemy_left_half_x
        valid_y = self.enemy_left_half_y
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        if unit.unit_type == TURRET:
                            if unit.upgraded:
                                left_val += 12
                            else:
                                left_val += 6
                        elif unit.unit_type == WALL:
                            if unit.upgraded:
                                left_val += 2
                            else:
                                left_val += 0.5
                        if unit.unit_type == SUPPORT:
                            if unit.upgraded:
                                left_val += 6
                            else: 
                                left_val += 4
                    left_val = 0
        right_val = 0
        valid_x = self.enemy_right_half_x
        valid_y = self.enemy_right_half_y
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        if unit.unit_type == TURRET:
                            if unit.upgraded:
                                right_val += 12
                            else:
                                right_val += 6
                        elif unit.unit_type == WALL:
                            if unit.upgraded:
                                right_val += 2
                            else:
                                right_val += 0.5
                        if unit.unit_type == SUPPORT:
                            if unit.upgraded:
                                right_val += 6
                            else: 
                                right_val += 4
        return left_val, right_val
                
    def remove_damaged(self, game_state):
        """
        Find all damaged turrets and walls, remove them, append the unit removed and location to be 
        added back on next turn to list
        """
        # get information of player's SP(0) & MP(1)
        my_resources = game_state.get_resources(player_index = 0)
        opponent_resources = game_state.get_resources(player_index = 1)

        if my_resources[0] >= 20:
            wall_threshold = 0.8
            turret_threshold = 0.64
        else: 
            wall_threshold = 0.2
            turret_threshold = 0.42

        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 0:
                        if unit.unit_type == WALL:
                            # if not(unit.upgraded):
                            #     if unit.health < 12:    
                            #         game_state.attempt_remove(location)
                            #         self.to_rebuild.append((unit.unit_type, location))
                            if unit.upgraded:
                                if unit.health < 120 * wall_threshold: 
                                    game_state.attempt_remove(location)
                                    self.to_rebuild.append((unit.unit_type, location))
                        #elif unit.unit_type == TURRET:
                         #   if unit.health < 75 * turret_threshold:    
                          #      game_state.attempt_remove(location)
                           #     self.to_rebuild.append((unit.unit_type, location))
                                    
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
        # First, place basic defenses
        self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                self.demolisher_line_strategy(game_state)
            else:
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time
                if game_state.turn_number % 2 == 1:
                    # To simplify we will just check sending them from back left and right
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                    game_state.attempt_spawn(SCOUT, best_location, 1000)

                # Lastly, if we have spare SP, let's build some supports
                support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(SUPPORT, support_locations)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[8, 12], [19, 12]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

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
    
    def detect_upgraded_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y) and (unit.upgraded):
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
        # # Let's record at what position we get scored on
        # state = json.loads(turn_string)
        # events = state["events"]
        # breaches = events["breach"]
        # for breach in breaches:
        #     location = breach[0]
        #     unit_owner_self = True if breach[4] == 1 else False
        #     # When parsing the frame data directly, 
        #     # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
        #     if not unit_owner_self:
        #         gamelib.debug_write("Got scored on at: {}".format(location))
        #         self.scored_on_locations.append(location)
        #         gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

        """
        events = state["events"]
        self_destructs = events["selfDestruct"]
        #p1 = state["p1Units"][4] # list of all my demolishers
        dead_units = state["death"]
        for self_destruct in self_destructs:
            location = self_destruct[0]
            unit_owner_self = True if self_destruct[5] == 1 else False
            if not unit_owner_self: # unit that self destructed was owned by the opponent
                if self_destruct[3] == 5:   # unit that self destructed was an interceptor
                        for demolisher in p1:
                            demolisher_position = [demolisher[0], demolisher[1]]
                            if demolisher_position in self_destruct[1]:
                                self.avoid_interceptor_path = True
        """
        state = json.loads(turn_string)
        events = state["events"]
        spawns = events["spawn"]
        turninfo = state["turnInfo"]
        opponent_mp = state["p2Stats"][2]
        self_destructs = events["selfDestruct"]
        deaths = events["death"]
        spawned = False
        if turninfo[0] == 1 and turninfo[2] == 0:
            for spawn in spawns:
                location = spawn[0]
                unit_owner_self = True if spawn[3] == 1 else False
                if not unit_owner_self:
                    self.opponent_spawn_locations.append((location[0], location[1]))
                    if spawn[1] == 4:
                        opponent_mp += 3
                        spawned = True
                    elif spawn[1] == 5:
                        opponent_mp += 1
                        spawned = True
                    elif spawn[1] == 3:
                        opponent_mp += 1
                        spawned = True
        if spawned:
            self.avg_sum += opponent_mp
            self.avg_count += 1
        
        for self_destruct in self_destructs:
            location = self_destruct[0]
            unit_owner_self = True if self_destruct[5] == 1 else False
            if not unit_owner_self: # unit that self destructed was owned by the opponent
                if self_destruct[3] == 5:
                    self.self_destruct_info.append((turninfo[1], turninfo[2], self_destruct[1]))
                    # gamelib.debug_write("self_destruct:", turninfo[1], turninfo[2], self_destruct[1])
        #for death in deaths:
            # gamelib.debug_write("death:", death, turninfo[1], turninfo[2])
         #   unit_owner_self = True if death[3] == 1 else False
          #  if unit_owner_self:
           #     if death[2] == 4 or death[2] == 3 or death[2] == 5:
            #        self.death_info.append((turninfo[1], turninfo[2], death[0]))
            # gamelib.debug_write(opponent_mp)
        


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
