import React, { useState } from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { LoginScreen } from '../screens/LoginScreen';
import { DashboardScreen } from '../screens/DashboardScreen';
import { AuditArticleScreen } from '../screens/AuditArticleScreen';
import { CatalogScreen } from '../screens/CatalogScreen';
import { TopAppBar } from '../components/layout/TopAppBar';
import { SidebarDrawer, ScreenRoute } from '../components/layout/SidebarDrawer';
import { colors } from '../utils/designTokens';

export const AppNavigator: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentRoute, setCurrentRoute] = useState<ScreenRoute>('Dashboard');
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [auditTargetArticleId, setAuditTargetArticleId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary[500]} />
      </View>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  const navigateToAuditWithArticle = (articleId: string) => {
    setAuditTargetArticleId(articleId);
    setCurrentRoute('AuditArticle');
  };

  const getScreenTitle = () => {
    switch (currentRoute) {
      case 'Dashboard':
        return '';
      case 'AuditArticle':
        return 'Auditoría de artículo';
      case 'Catalog':
        return 'Catálogo de artículos';
    }
  };

  return (
    <View style={styles.container}>
      {/* Top Application Bar */}
      <TopAppBar
        onOpenDrawer={() => setIsDrawerOpen(true)}
        title={getScreenTitle()}
      />

      {/* Screen Views */}
      <View style={styles.screenWrapper}>
        {currentRoute === 'Dashboard' && (
          <DashboardScreen
            onNavigateToAudit={() => {
              setAuditTargetArticleId(null);
              setCurrentRoute('AuditArticle');
            }}
            onNavigateToCatalog={() => setCurrentRoute('Catalog')}
          />
        )}

        {currentRoute === 'AuditArticle' && (
          <AuditArticleScreen
            initialArticleId={auditTargetArticleId}
            onAuditCompleted={() => {
              setAuditTargetArticleId(null);
              setCurrentRoute('Dashboard');
            }}
          />
        )}

        {currentRoute === 'Catalog' && (
          <CatalogScreen
            onSelectArticle={(id) => navigateToAuditWithArticle(id)}
          />
        )}
      </View>

      {/* Navigation Slide-Over Drawer */}
      <SidebarDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        currentRoute={currentRoute}
        onNavigate={(route) => {
          if (route !== 'AuditArticle') {
            setAuditTargetArticleId(null);
          }
          setCurrentRoute(route);
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.base,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: colors.background.base,
    alignItems: 'center',
    justifyContent: 'center',
  },
  screenWrapper: {
    flex: 1,
  },
});
