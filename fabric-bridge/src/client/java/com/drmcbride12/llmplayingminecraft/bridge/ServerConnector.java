package com.drmcbride12.llmplayingminecraft.bridge;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;

final class ServerConnector {
	private ServerConnector() {
	}

	@SuppressWarnings({"unchecked", "rawtypes"})
	static boolean connect(Object minecraftClient, String serverAddress) {
		try {
			Object currentScreen = ReflectionAccess.field(minecraftClient, "screen", "field_1755").orElse(null);
			Class<?> screenClass = Class.forName("net.minecraft.client.gui.screens.Screen");
			Class<?> minecraftClass = Class.forName("net.minecraft.client.Minecraft");
			Class<?> addressClass = Class.forName("net.minecraft.client.multiplayer.resolver.ServerAddress");
			Class<?> serverDataClass = Class.forName("net.minecraft.client.multiplayer.ServerData");
			Class<?> serverDataTypeClass = Class.forName("net.minecraft.client.multiplayer.ServerData$Type");
			Class<?> transferStateClass = Class.forName("net.minecraft.client.multiplayer.TransferState");
			Class<?> connectScreenClass = Class.forName("net.minecraft.client.gui.screens.ConnectScreen");

			Object address = addressClass.getMethod("parseString", String.class).invoke(null, serverAddress);
			Object type = Enum.valueOf((Class<Enum>) serverDataTypeClass.asSubclass(Enum.class), "OTHER");
			Constructor<?> serverDataConstructor = serverDataClass.getConstructor(String.class, String.class, serverDataTypeClass);
			Object serverData = serverDataConstructor.newInstance("LLM Bridge Server", serverAddress, type);
			Method startConnecting = connectScreenClass.getMethod(
				"startConnecting",
				screenClass,
				minecraftClass,
				addressClass,
				serverDataClass,
				boolean.class,
				transferStateClass
			);
			startConnecting.invoke(null, currentScreen, minecraftClient, address, serverData, false, null);
			return true;
		} catch (ReflectiveOperationException error) {
			System.err.println("[llm-playing-minecraft] Server connect reflection failed: " + error);
			return false;
		}
	}
}
