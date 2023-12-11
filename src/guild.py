class HypixelGuild:
	def __init__(self, data: dict):
		self._id = data['_id']
		self.name = data['name']
		self.name_lower = data['name_lower']
		self.created_raw = data['created']
		self.members = HypixelGuildMembers(data['members'])


class HypixelGuildMembers:
	def __init__(self, data: dict):
		self.members = [HypixelGuildMember(p) for p in data]


class HypixelGuildMember:
	def __init__(self, data: dict):
		self.uuid = data['uuid']
		self.rank = data['rank']
		self.joined_raw = data['joined']
		self.quest_participation = data.get('questParticipation', 0)
		self.exp_history = data['expHistory']
