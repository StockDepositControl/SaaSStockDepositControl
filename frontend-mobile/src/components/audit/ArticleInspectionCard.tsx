import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { ArticuloAuditorView } from '../../types/article';
import { StatusBadge } from '../ui/StatusBadge';
import { FefoAlertBanner } from './FefoAlertBanner';
import { colors } from '../../utils/designTokens';

interface ArticleInspectionCardProps {
  article: ArticuloAuditorView;
}

export const ArticleInspectionCard: React.FC<ArticleInspectionCardProps> = ({ article }) => {
  const brandAndFamily = [article.des_marca || 'Sin marca', article.des_familia || 'General']
    .filter(Boolean)
    .join(' · ');

  return (
    <View style={styles.card}>
      {/* Top Identity Row */}
      <View style={styles.topRow}>
        <View style={styles.identityBox}>
          <Text style={styles.articleName} numberOfLines={2}>
            {article.des_articulo}
          </Text>
          <Text style={styles.subtitleText}>{brandAndFamily}</Text>
        </View>
        <StatusBadge status={article.status} />
      </View>

      {/* Horizontal Divider */}
      <View style={styles.divider} />

      {/* Specs & System Stock Row */}
      <View style={styles.specsRow}>
        {/* Left: CÓDIGO */}
        <View style={styles.specColumn}>
          <Text style={styles.specLabel}>CÓDIGO</Text>
          <Text style={styles.specCode}>{article.code || article.barcode}</Text>
        </View>

        {/* Right: STOCK EN SISTEMA */}
        <View style={[styles.specColumn, { alignItems: 'flex-end' }]}>
          <Text style={styles.specLabel}>STOCK EN SISTEMA</Text>
          <View style={styles.stockBox}>
            <Text style={styles.stockNumber}>{article.stock_real}</Text>
            <Text style={styles.stockUnit}> uds.</Text>
          </View>
        </View>
      </View>

      {/* FEFO Expiry Alert Banner */}
      <FefoAlertBanner expirationDate={article.fefo_expiration_date} />
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.background.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.background.surfaceMuted,
    padding: 16,
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  identityBox: {
    flex: 1,
    paddingRight: 12,
  },
  articleName: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
  },
  subtitleText: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.text.muted,
    marginTop: 3,
  },
  divider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 14,
  },
  specsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  specColumn: {
    justifyContent: 'flex-end',
  },
  specLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.text.muted,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  specCode: {
    fontSize: 13,
    fontWeight: '700',
    fontFamily: Platform?.OS === 'ios' ? 'Courier' : 'monospace',
    color: colors.text.primary,
  },
  stockBox: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  stockNumber: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.text.primary,
    fontFamily: Platform?.OS === 'ios' ? 'Courier' : 'monospace',
  },
  stockUnit: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.text.muted,
  },
});
