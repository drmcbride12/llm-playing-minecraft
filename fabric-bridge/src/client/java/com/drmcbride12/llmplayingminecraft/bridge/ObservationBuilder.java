package com.drmcbride12.llmplayingminecraft.bridge;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

final class ObservationBuilder {
	private ObservationBuilder() {
	}

	static String build(Object minecraftClient, String clientId) {
		Object player = ReflectionAccess.field(minecraftClient, "player", "field_1724").orElse(null);
		JsonObject root = new JsonObject();
		root.addProperty("client_id", clientId);
		root.addProperty("summary", player == null ? "Client is not in a world." : "Client is in world and awaiting Baritone direction.");

		JsonObject playerJson = new JsonObject();
		if (player != null) {
			playerJson.addProperty("position", position(player));
			ReflectionAccess.callNumber(player, "getHealth", "method_6032").ifPresent(value -> playerJson.addProperty("health", value));
			ReflectionAccess.call(player, "getName", "method_5477").ifPresent(value -> playerJson.addProperty("name", value.toString()));
		}
		root.add("player", playerJson);

		JsonObject baritoneJson = new JsonObject();
		baritoneJson.addProperty("status", BaritoneCommandExecutor.available() ? "available" : "missing");
		baritoneJson.addProperty("profile", "bold");
		root.add("baritone", baritoneJson);

		JsonArray inventory = new JsonArray();
		ReflectionAccess.call(player, "getInventory", "method_31548").ifPresent(value -> inventory.add(value.toString()));
		if (inventory.isEmpty()) {
			inventory.add("unknown");
		}
		root.add("inventory", inventory);

		root.add("important_blocks", new JsonArray());
		root.add("entities", new JsonArray());
		root.add("hazards", new JsonArray());
		root.add("regions", new JsonArray());
		root.add("memory", new JsonArray());
		return root.toString();
	}

	private static String position(Object player) {
		double x = ReflectionAccess.callNumber(player, "getX", "method_23317").orElse(Double.NaN);
		double y = ReflectionAccess.callNumber(player, "getY", "method_23318").orElse(Double.NaN);
		double z = ReflectionAccess.callNumber(player, "getZ", "method_23321").orElse(Double.NaN);
		if (Double.isNaN(x) || Double.isNaN(y) || Double.isNaN(z)) {
			return "unknown";
		}
		return Math.round(x) + " " + Math.round(y) + " " + Math.round(z);
	}
}
