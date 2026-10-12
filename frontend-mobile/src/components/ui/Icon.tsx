import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export type IconName =
  | 'clipboard-check'
  | 'menu'
  | 'eye'
  | 'eye-off'
  | 'search'
  | 'camera'
  | 'arrow-right'
  | 'layout-grid'
  | 'list-filter'
  | 'log-out'
  | 'calendar'
  | 'alert-triangle'
  | 'alert-circle'
  | 'check'
  | 'chevron-down'
  | 'package'
  | 'x'
  | 'flash';

interface IconProps {
  name: IconName;
  size?: number;
  color?: string;
}

export const Icon: React.FC<IconProps> = ({ name, size = 20, color = '#475569' }) => {
  const getSymbol = () => {
    switch (name) {
      case 'clipboard-check':
        return '📋';
      case 'menu':
        return '☰';
      case 'eye':
        return '👁';
      case 'eye-off':
        return '🙈';
      case 'search':
        return '🔍';
      case 'camera':
        return '📷';
      case 'arrow-right':
        return '→';
      case 'layout-grid':
        return '⊞';
      case 'list-filter':
        return '☷';
      case 'log-out':
        return '🚪';
      case 'calendar':
        return '📅';
      case 'alert-triangle':
        return '⚠';
      case 'alert-circle':
        return 'ⓘ';
      case 'check':
        return '✓';
      case 'chevron-down':
        return '▼';
      case 'package':
        return '📦';
      case 'x':
        return '✕';
      case 'flash':
        return '⚡';
      default:
        return '•';
    }
  };

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Text
        style={{
          fontSize: Math.round(size * 0.85),
          color,
          textAlign: 'center',
          lineHeight: size,
          fontWeight: 'bold',
        }}
      >
        {getSymbol()}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
