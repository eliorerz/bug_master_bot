from .channel_configuration_command import ChannelConfigurationCommand
from .apply_command import ApplyCommand
from .help_command import HelpCommand
from .statistics_command import StatisticsCommand


class SupportedCommands:
    HELP_COMMAND = "help"
    GET_CHANNEL_CONFIGURATIONS_COMMAND = "config"
    STATISTICS_COMMAND = "stats"
    APPLY_COMMAND = "apply"

    @classmethod
    def get_commands_map(cls):
        return {
            cls.GET_CHANNEL_CONFIGURATIONS_COMMAND: ChannelConfigurationCommand,
            cls.HELP_COMMAND: HelpCommand,
            cls.STATISTICS_COMMAND: StatisticsCommand,
            cls.APPLY_COMMAND: ApplyCommand,
        }


class NotSupportedCommandError(Exception):
    def __init__(self, message, command: str = ""):
        super().__init__(self, message)
        self.command = command
        self.message = message