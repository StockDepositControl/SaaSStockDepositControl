import React from 'react';
import { View, Text, Pressable, StyleSheet, SafeAreaView, Platform, StatusBar } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { Icon } from '../ui/Icon';
import { colors } from '../../utils/designTokens';

interface TopAppBarProps {
  onOpenDrawer: () => void;
  title?: string;
}

export const TopAppBar: React.FC<TopAppBarProps> = ({ onOpenDrawer, title }) => {
  const { session } = useAuth();
  const initials = session?.initials || 'OP';

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {/* Left Hamburger Button */}
        <Pressable
          onPress={onOpenDrawer}
          style={({ pressed }) => [styles.iconButton, pressed && styles.iconButtonPressed]}
          hitSlop={10}
        >
          <Icon name="menu" size={22} color="#F8FAFC" />
        </Pressable>

        {/* Optional Title */}
        {title ? (
          <Text style={styles.titleText} numberOfLines={1}>
            {title}
          </Text>
        ) : (
          <View style={{ flex: 1 }} />
        )}

        {/* Right User Avatar Initials */}
        <Pressable
          onPress={onOpenDrawer}
          style={styles.avatarCircle}
          hitSlop={8}
        >
          <Text style={styles.avatarText}>{initials}</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: colors.background.darkSurface,
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
  container: {
    height: 56,
    backgroundColor: colors.background.darkSurface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
  },
  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconButtonPressed: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  titleText: {
    flex: 1,
    fontSize: 16,
    fontWeight: '700',
    color: '#F8FAFC',
    textAlign: 'center',
    marginHorizontal: 8,
  },
  avatarCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primary[500],
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
