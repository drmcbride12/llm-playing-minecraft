package com.drmcbride12.llmplayingminecraft.bridge;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;

public final class LlmPlayingMinecraftBridgeClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		BridgeRuntime runtime = new BridgeRuntime(BridgeConfig.load());
		ClientTickEvents.END_CLIENT_TICK.register(runtime::onClientTick);
		System.out.println("[llm-playing-minecraft] Client bridge loaded for " + runtime.clientId());
	}
}
