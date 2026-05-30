package com.drmcbride12.llmplayingminecraft.bridge;

final class ChatExecutor {
	private ChatExecutor() {
	}

	static void send(Object minecraftClient, String message) {
		Object player = ReflectionAccess.field(minecraftClient, "player", "field_1724").orElse(null);
		if (player == null) {
			return;
		}

		ReflectionAccess.call(player, new String[]{"sendChatMessage", "method_3142"}, new Class<?>[]{String.class}, new Object[]{message});
	}
}
