package com.drmcbride12.llmplayingminecraft.bridge;

import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;
import java.util.UUID;

final class BridgeConfig {
	private static final String FILE_NAME = "llm-playing-minecraft-bridge.properties";

	final String clientId;
	final String controllerUrl;
	final String autoConnectServer;
	final int reportTicks;
	final int pollTicks;

	private BridgeConfig(String clientId, String controllerUrl, String autoConnectServer, int reportTicks, int pollTicks) {
		this.clientId = clientId;
		this.controllerUrl = stripTrailingSlash(controllerUrl);
		this.autoConnectServer = autoConnectServer.trim();
		this.reportTicks = reportTicks;
		this.pollTicks = pollTicks;
	}

	static BridgeConfig load() {
		Path path = FabricLoader.getInstance().getConfigDir().resolve(FILE_NAME);
		Properties properties = new Properties();

		if (Files.exists(path)) {
			try (InputStream input = Files.newInputStream(path)) {
				properties.load(input);
			} catch (IOException error) {
				System.err.println("[llm-playing-minecraft] Could not read config: " + error.getMessage());
			}
		}

		boolean changed = false;
		if (!properties.containsKey("client_id")) {
			properties.setProperty("client_id", "client-" + UUID.randomUUID());
			changed = true;
		}
		if (!properties.containsKey("controller_url")) {
			properties.setProperty("controller_url", "http://127.0.0.1:8765");
			changed = true;
		}
		if (!properties.containsKey("auto_connect_server")) {
			properties.setProperty("auto_connect_server", "");
			changed = true;
		}
		if (!properties.containsKey("report_ticks")) {
			properties.setProperty("report_ticks", "40");
			changed = true;
		}
		if (!properties.containsKey("poll_ticks")) {
			properties.setProperty("poll_ticks", "20");
			changed = true;
		}

		if (changed) {
			try {
				Files.createDirectories(path.getParent());
				try (OutputStream output = Files.newOutputStream(path)) {
					properties.store(output, "LLM Playing Minecraft bridge config");
				}
			} catch (IOException error) {
				System.err.println("[llm-playing-minecraft] Could not write config: " + error.getMessage());
			}
		}

		return new BridgeConfig(
			properties.getProperty("client_id"),
			properties.getProperty("controller_url"),
			properties.getProperty("auto_connect_server", ""),
			intProperty(properties, "report_ticks", 40),
			intProperty(properties, "poll_ticks", 20)
		);
	}

	private static int intProperty(Properties properties, String name, int fallback) {
		try {
			return Math.max(1, Integer.parseInt(properties.getProperty(name, Integer.toString(fallback))));
		} catch (NumberFormatException error) {
			return fallback;
		}
	}

	private static String stripTrailingSlash(String value) {
		while (value.endsWith("/")) {
			value = value.substring(0, value.length() - 1);
		}
		return value;
	}
}
