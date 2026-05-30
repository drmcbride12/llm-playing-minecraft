package com.drmcbride12.llmplayingminecraft.bridge;

import net.fabricmc.api.ClientModInitializer;

public final class LlmPlayingMinecraftBridgeClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		System.out.println("[llm-playing-minecraft] Client bridge loaded.");
	}
}
