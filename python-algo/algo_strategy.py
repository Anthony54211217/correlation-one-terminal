from gamelib import AlgoCore, GameState, debug_write
from math import inf
from random import choice, randrange, seed
from sys import maxsize

LEFT = 0
RIGHT = 1

class Entity:
    def __init__(self, shorthand, location, count=1):
        self.shorthand = shorthand
        self.location = location
        self.count = count
        self.status = True
        self.spawn_count = 0

    def get_health(self, game_state):
        for unit in game_state.game_map[self.location]:
            if unit.stationary:
                return unit.health

        return 0

    def get_max_health(self, game_state):
        for unit in game_state.game_map[self.location]:
            if unit.stationary:
                return unit.max_health

        return 0

    def is_spawned(self, game_state):
        return game_state.contains_stationary_unit(self.location)

    def is_upgraded(self, game_state):
        for unit in game_state.game_map[self.location]:
            if unit.stationary and unit.upgraded:
                return True

        return False

    def spawn(self, game_state):
        if not self.status or self.is_spawned(game_state):
            return True

        self.spawn_count += 1

        return game_state.attempt_spawn(
            self.shorthand,
            self.location,
            self.count,
        )

    def upgrade(self, game_state):
        if not self.status or self.is_upgraded(game_state):
            return True

        return game_state.attempt_upgrade(self.location)

    def remove(self, game_state):
        return game_state.attempt_remove(self.location)


class AlgoStrategy(AlgoCore):
    @classmethod
    def main(cls):
        seed_ = randrange(maxsize)
        seed(seed_)
        debug_write(f'Seed: {seed_}')

        algo = AlgoStrategy()
        algo.start()

    def on_game_start(self, config):
        super().on_game_start(config)

        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, SP, MP

        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        SP = 0
        MP = 1
        self.walls = []

        for i, j in zip(range(14), reversed(range(14, 28))):
            self.walls.append(Entity(WALL, [i, 13]))
            self.walls.append(Entity(WALL, [j, 13]))

        self.wall_map = {}

        for wall in self.walls:
            self.wall_map[wall.location[0]] = wall

        self.turrets = [
            Entity(TURRET, [1, 12]),
            Entity(TURRET, [26, 12]),
            Entity(TURRET, [2, 12]),
            Entity(TURRET, [25, 12]),
            Entity(TURRET, [2, 11]),
            Entity(TURRET, [25, 11]),
        ]
        self.supports = [
            Entity(SUPPORT, [13, 12]),
            Entity(SUPPORT, [14, 12]),
            Entity(SUPPORT, [12, 12]),
            Entity(SUPPORT, [15, 12]),
        ]
        self.builds = [
            *(wall for wall in self.walls),
            *(turret for turret in self.turrets[:4]),
            *(support for support in self.supports[:2]),
            *(turret for turret in self.turrets[4:]),
            *(support for support in self.supports[2:]),
        ]
        self.upgraded_wall_rebuild_threshold = 0.6
        self.turret_rebuild_threshold = 0.35
        self.attack_direction = LEFT
        self.attack_locations = {
            LEFT: [16, 2],
            RIGHT: [11, 2],
        }
        self.attack_walls = {
            LEFT: self.wall_map[5],
            RIGHT: self.wall_map[22],
        }
        self.attack_threshold = 16
        self.attack_walls[self.attack_direction].status = False
        self.previous_enemy_health = inf

    def on_turn(self, turn_state):
        game_state = GameState(self.config, turn_state)

        debug_write(f'Performing turn {game_state.turn_number}...')
        game_state.suppress_warnings(True)
        self.defend(game_state)
        self.attack(game_state)
        self.previous_enemy_health = game_state.enemy_health
        game_state.submit_turn()

    def defend(self, game_state):
        def upgrade():
            for support in self.supports:
                support.upgrade(game_state)

            for wall in self.walls:
                if wall.spawn_count > 1:
                    wall.upgrade(game_state)

            for turret in self.turrets:
                if turret.spawn_count > 1:
                    turret.upgrade(game_state)

        upgrade()

        for wall in self.walls:
            if wall.is_spawned(game_state):
                min_health = self.upgraded_wall_rebuild_threshold \
                    * wall.get_max_health(game_state)

                if wall.is_upgraded(game_state) \
                        and wall.get_health(game_state) < min_health:
                    wall.remove(game_state)

        for turret in self.turrets:
            if turret.is_spawned(game_state):
                min_health = self.turret_rebuild_threshold \
                    * turret.get_max_health(game_state)

                if turret.get_health(game_state) < min_health:
                    turret.remove(game_state)

        for build in self.builds:
            if not build.spawn(game_state):
                break

        upgrade()

    def attack(self, game_state):
        if game_state.enemy_health >= self.previous_enemy_health:
            counter = [0, 0]

            for location in game_state.game_map:
                if game_state.contains_stationary_unit(location):
                    for unit in game_state.game_map[location]:
                        if unit.player_index == 1 and unit.unit_type == TURRET:
                            if location[0] < 14:
                                counter[LEFT] += 1
                            else:
                                counter[RIGHT] += 1

            if counter[RIGHT] > counter[LEFT]:
                self.attack_direction = LEFT
            elif counter[RIGHT] < counter[LEFT]:
                self.attack_direction = RIGHT
            else:
                self.attack_direction = choice([LEFT, RIGHT])

        wall = self.attack_walls[self.attack_direction]
        wall.status = False

        if wall.is_spawned(game_state):
            wall.remove(game_state)
        elif game_state.enemy_health < self.previous_enemy_health:
            game_state.attempt_spawn(
                SCOUT,
                self.attack_locations[self.attack_direction],
                1000,
            )
        elif game_state.get_resource(MP) >= self.attack_threshold:
            game_state.attempt_spawn(
                DEMOLISHER,
                self.attack_locations[self.attack_direction],
                1000,
            )
            game_state.attempt_spawn(
                SCOUT,
                self.attack_locations[self.attack_direction],
                1000,
            )

        anti_wall = self.attack_walls[not self.attack_direction]
        anti_wall.status = True

        if not anti_wall.is_spawned(game_state):
            anti_wall.spawn(game_state)


if __name__ == '__main__':
    AlgoStrategy.main()
