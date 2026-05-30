package com.drmcbride12.llmplayingminecraft.bridge;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Optional;

final class ReflectionAccess {
	private ReflectionAccess() {
	}

	static Optional<Object> field(Object target, String... names) {
		if (target == null) {
			return Optional.empty();
		}
		Class<?> type = target.getClass();
		for (String name : names) {
			Class<?> current = type;
			while (current != null) {
				try {
					Field field = current.getDeclaredField(name);
					field.setAccessible(true);
					return Optional.ofNullable(field.get(target));
				} catch (ReflectiveOperationException ignored) {
					current = current.getSuperclass();
				}
			}
		}
		return Optional.empty();
	}

	static Optional<Object> call(Object target, String... names) {
		return call(target, names, new Class<?>[0], new Object[0]);
	}

	static Optional<Object> call(Object target, String[] names, Class<?>[] parameterTypes, Object[] args) {
		if (target == null) {
			return Optional.empty();
		}
		Class<?> type = target.getClass();
		for (String name : names) {
			Class<?> current = type;
			while (current != null) {
				try {
					Method method = current.getDeclaredMethod(name, parameterTypes);
					method.setAccessible(true);
					return Optional.ofNullable(method.invoke(target, args));
				} catch (ReflectiveOperationException ignored) {
					current = current.getSuperclass();
				}
			}
		}
		return Optional.empty();
	}

	static Optional<Double> callNumber(Object target, String... names) {
		return call(target, names).flatMap(value -> {
			if (value instanceof Number number) {
				return Optional.of(number.doubleValue());
			}
			return Optional.empty();
		});
	}
}
