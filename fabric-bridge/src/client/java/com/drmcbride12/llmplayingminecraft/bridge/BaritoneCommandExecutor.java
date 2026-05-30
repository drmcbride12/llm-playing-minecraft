package com.drmcbride12.llmplayingminecraft.bridge;

import java.lang.reflect.Method;

final class BaritoneCommandExecutor {
	private BaritoneCommandExecutor() {
	}

	static boolean available() {
		try {
			Class.forName("baritone.api.BaritoneAPI");
			return true;
		} catch (ClassNotFoundException error) {
			return false;
		}
	}

	static boolean execute(String command) {
		String normalized = command.startsWith("#") ? command.substring(1) : command;
		try {
			Class<?> apiClass = Class.forName("baritone.api.BaritoneAPI");
			Object provider = apiClass.getMethod("getProvider").invoke(null);
			Object baritone = provider.getClass().getMethod("getPrimaryBaritone").invoke(provider);
			Object manager = baritone.getClass().getMethod("getCommandManager").invoke(baritone);
			Method execute = manager.getClass().getMethod("execute", String.class);
			Object result = execute.invoke(manager, normalized);
			return !(result instanceof Boolean) || (Boolean) result;
		} catch (ReflectiveOperationException error) {
			System.err.println("[llm-playing-minecraft] Baritone reflection failed: " + error);
			return false;
		}
	}
}
