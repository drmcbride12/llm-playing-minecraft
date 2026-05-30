package com.drmcbride12.llmplayingminecraft.bridge;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Optional;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

final class BridgeRuntime {
	private final BridgeConfig config;
	private final HttpClient httpClient = HttpClient.newBuilder()
		.connectTimeout(Duration.ofSeconds(2))
		.build();
	private final ExecutorService ioExecutor = Executors.newSingleThreadExecutor(task -> {
		Thread thread = new Thread(task, "llm-playing-minecraft-bridge");
		thread.setDaemon(true);
		return thread;
	});
	private final Queue<BridgeCommand> pendingCommands = new ConcurrentLinkedQueue<>();
	private final AtomicBoolean reporting = new AtomicBoolean(false);
	private final AtomicBoolean polling = new AtomicBoolean(false);
	private int ticks;
	private long lastCommandId;

	BridgeRuntime(BridgeConfig config) {
		this.config = config;
	}

	String clientId() {
		return config.clientId;
	}

	void onClientTick(Object minecraftClient) {
		ticks++;
		executePending(minecraftClient);

		if (ticks % config.reportTicks == 0 && reporting.compareAndSet(false, true)) {
			String observation = ObservationBuilder.build(minecraftClient, config.clientId);
			ioExecutor.execute(() -> {
				try {
					postObservation(observation);
				} catch (Exception error) {
					System.err.println("[llm-playing-minecraft] Observation post failed: " + error);
				} finally {
					reporting.set(false);
				}
			});
		}

		if (ticks % config.pollTicks == 0 && polling.compareAndSet(false, true)) {
			ioExecutor.execute(() -> {
				try {
					pollCommand().ifPresent(pendingCommands::add);
				} catch (Exception error) {
					System.err.println("[llm-playing-minecraft] Command poll failed: " + error);
				} finally {
					polling.set(false);
				}
			});
		}
	}

	private void postObservation(String observationJson) throws Exception {
		HttpRequest request = HttpRequest.newBuilder()
			.uri(URI.create(config.controllerUrl + "/api/clients/" + url(config.clientId) + "/observation"))
			.timeout(Duration.ofSeconds(5))
			.header("Content-Type", "application/json")
			.POST(HttpRequest.BodyPublishers.ofString(observationJson))
			.build();
		httpClient.send(request, HttpResponse.BodyHandlers.discarding());
	}

	private Optional<BridgeCommand> pollCommand() throws Exception {
		HttpRequest request = HttpRequest.newBuilder()
			.uri(URI.create(config.controllerUrl + "/api/clients/" + url(config.clientId) + "/command?last_id=" + lastCommandId))
			.timeout(Duration.ofSeconds(5))
			.GET()
			.build();
		HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
		if (response.statusCode() != 200 || response.body().isBlank()) {
			return Optional.empty();
		}

		JsonObject payload = JsonParser.parseString(response.body()).getAsJsonObject();
		if (!payload.has("command") || payload.get("command").isJsonNull()) {
			return Optional.empty();
		}

		JsonObject command = payload.getAsJsonObject("command");
		long commandId = command.get("id").getAsLong();
		if (commandId <= lastCommandId) {
			return Optional.empty();
		}

		lastCommandId = commandId;
		String baritoneCommand = optionalString(command, "baritone_command");
		String chat = optionalString(command, "chat");
		return Optional.of(new BridgeCommand(commandId, baritoneCommand, chat));
	}

	private void executePending(Object minecraftClient) {
		BridgeCommand command;
		while ((command = pendingCommands.poll()) != null) {
			if (command.baritoneCommand() != null && !command.baritoneCommand().isBlank()) {
				boolean executed = BaritoneCommandExecutor.execute(command.baritoneCommand());
				if (executed) {
					System.out.println("[llm-playing-minecraft] Executed Baritone command " + command.id() + ": " + command.baritoneCommand());
				} else {
					System.err.println("[llm-playing-minecraft] Could not execute Baritone command: " + command.baritoneCommand());
				}
			}
			if (command.chat() != null && !command.chat().isBlank()) {
				if (ChatExecutor.send(minecraftClient, command.chat())) {
					System.out.println("[llm-playing-minecraft] Sent chat command " + command.id() + ": " + command.chat());
				} else {
					System.err.println("[llm-playing-minecraft] Could not send chat command: " + command.chat());
				}
			}
		}
	}

	private static String optionalString(JsonObject object, String name) {
		if (!object.has(name) || object.get(name).isJsonNull()) {
			return null;
		}
		return object.get(name).getAsString();
	}

	private static String url(String value) {
		return URLEncoder.encode(value, StandardCharsets.UTF_8);
	}
}
