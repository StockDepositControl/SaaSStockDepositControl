import React from 'react';
import {
  View,
  Text,
  Pressable,
  Modal,
  StyleSheet,
  SafeAreaView,
  Alert,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { Icon } from '../ui/Icon';
import { colors } from '../../utils/designTokens';

export type ScreenRoute = 'Dashboard' | 'AuditArticle' | 'Catalog';

interface SidebarDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  currentRoute: ScreenRoute;
  onNavigate: (route: ScreenRoute) => void;
}

export const SidebarDrawer: React.FC<SidebarDrawerProps> = ({
  isOpen,
  onClose,
  currentRoute,
  onNavigate,
}) => {
  const { session, logout } = useAuth();

  const handleLogout = () => {
    Alert.alert(
      'Cerrar sesión',
      '¿Estás seguro de que deseás cerrar la sesión actual?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Cerrar sesión',
          style: 'destructive',
          onPress: async () => {
            onClose();
            await logout();
          },
        },
      ]
    );
  };

  const navItems: { route: ScreenRoute; label: string; icon: 'layout-grid' | 'clipboard-check' | 'list-filter' }[] = [
    { route: 'Dashboard', label: 'Panel principal', icon: 'layout-grid' },
    { route: 'AuditArticle', label: 'Auditoría de artículo', icon: 'clipboard-check' },
    { route: 'Catalog', label: 'Catálogo de artículos', icon: 'list-filter' },
  ];

  return (
    <Modal
      visible={isOpen}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        {/* Backdrop tap to dismiss */}
        <Pressable style={styles.backdrop} onPress={onClose} />

        {/* Drawer Content */}
        <SafeAreaView style={styles.drawerPanel}>
          {/* User Profile Header */}
          <View style={styles.userHeader}>
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarText}>{session?.initials || 'LO'}</Text>
            </View>
            <View style={styles.userInfo}>
              <Text style={styles.userName} numberOfLines={1}>
                {session?.displayName || 'Luis Operario'}
              </Text>
              <View
                style={[
                  styles.roleBadge,
                  session?.role === 'supervisor'
                    ? styles.roleBadgeSupervisor
                    : styles.roleBadgeAuditor,
                ]}
              >
                <Text
                  style={[
                    styles.roleBadgeText,
                    session?.role === 'supervisor'
                      ? styles.roleBadgeTextSupervisor
                      : styles.roleBadgeTextAuditor,
                  ]}
                >
                  {session?.role?.toUpperCase() || 'AUDITOR'}
                </Text>
              </View>
            </View>
          </View>

          {/* Navigation Links */}
          <View style={styles.navSection}>
            {navItems.map((item) => {
              const isActive = currentRoute === item.route;
              return (
                <Pressable
                  key={item.route}
                  onPress={() => {
                    onNavigate(item.route);
                    onClose();
                  }}
                  style={({ pressed }) => [
                    styles.navItem,
                    isActive && styles.navItemActive,
                    pressed && !isActive && styles.navItemPressed,
                  ]}
                >
                  {isActive && <View style={styles.activeIndicator} />}
                  <View style={styles.navIconBox}>
                    <Icon
                      name={item.icon}
                      size={18}
                      color={isActive ? '#FFFFFF' : '#94A3B8'}
                    />
                  </View>
                  <Text
                    style={[
                      styles.navItemText,
                      isActive ? styles.navItemTextActive : styles.navItemTextInactive,
                    ]}
                  >
                    {item.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {/* Drawer Footer with Logout */}
          <View style={styles.footerSection}>
            <Pressable
              onPress={handleLogout}
              style={({ pressed }) => [
                styles.logoutButton,
                pressed && styles.logoutButtonPressed,
              ]}
            >
              <Icon name="log-out" size={18} color="#94A3B8" />
              <Text style={styles.logoutText}>Cerrar sesión</Text>
            </Pressable>
          </View>
        </SafeAreaView>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    flexDirection: 'row',
  },
  backdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  drawerPanel: {
    width: '78%',
    maxWidth: 300,
    height: '100%',
    backgroundColor: colors.background.drawerSurface,
    borderRightWidth: 1,
    borderRightColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'space-between',
  },
  userHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 24,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
    gap: 12,
  },
  avatarCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.primary[500],
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  roleBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  roleBadgeAuditor: {
    backgroundColor: '#E2E8F0',
  },
  roleBadgeSupervisor: {
    backgroundColor: '#E0E7FF',
  },
  roleBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  roleBadgeTextAuditor: {
    color: '#0F172A',
  },
  roleBadgeTextSupervisor: {
    color: '#3730A3',
  },
  navSection: {
    flex: 1,
    paddingHorizontal: 12,
    paddingTop: 16,
    gap: 6,
  },
  navItem: {
    height: 48,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    position: 'relative',
  },
  navItemActive: {
    backgroundColor: colors.background.drawerItemActive,
  },
  navItemPressed: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  activeIndicator: {
    position: 'absolute',
    left: 0,
    top: 12,
    bottom: 12,
    width: 4,
    borderRadius: 2,
    backgroundColor: '#3B82F6',
  },
  navIconBox: {
    width: 28,
    alignItems: 'center',
    marginRight: 8,
  },
  navItemText: {
    fontSize: 14,
  },
  navItemTextActive: {
    fontWeight: '700',
    color: '#FFFFFF',
  },
  navItemTextInactive: {
    fontWeight: '500',
    color: 'rgba(255, 255, 255, 0.7)',
  },
  footerSection: {
    paddingHorizontal: 16,
    paddingVertical: 18,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  logoutButton: {
    height: 48,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    borderRadius: 10,
    gap: 10,
  },
  logoutButtonPressed: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  logoutText: {
    fontSize: 14,
    fontWeight: '500',
    color: 'rgba(255, 255, 255, 0.7)',
  },
});
