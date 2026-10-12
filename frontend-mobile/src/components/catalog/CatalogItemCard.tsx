import React from 'react';
import { View, Text, Pressable, StyleSheet, Platform } from 'react-native';
import { ArticuloAuditorView } from '../../types/article';
import { StatusBadge } from '../ui/StatusBadge';
import { Icon } from '../ui/Icon';
import { colors } from '../../utils/designTokens';

interface CatalogItemCardProps {
  item: ArticuloAuditorView;
  onPress: () => void;
}

export const CatalogItemCard: React.FC<CatalogItemCardProps> = ({ item, onPress }) => {
  const brandAndFamily = [item.des_marca || 'Sin marca', item.des_familia || 'General']
    .filter(Boolean)
    .join(' · ');

  const isZeroStock = item.stock_real === 0;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
    >
      {/* Left Column: Article Name & Details */}
      <View style={styles.leftColumn}>
        <Text style={styles.articleName} numberOfLines={2}>
          {item.des_articulo}
        </Text>
        <Text style={styles.detailsSubtitle} numberOfLines={1}>
          {brandAndFamily}
        </Text>
      </View>

      {/* Right Column: Status & Stock */}
      <View style={styles.rightColumn}>
        <StatusBadge status={item.status} variant="neutral" />

        {/* Stock Count Display */}
        <View style={styles.stockBox}>
          {isZeroStock ? (
            <View style={styles.zeroStockRow}>
              <Icon name="alert-triangle" size={13} color="#DC2626" />
              <Text style={styles.zeroStockText}> 0 uds.</Text>
            </View>
          ) : (
            <View style={styles.normalStockRow}>
              <Text style={styles.normalStockNumber}>{item.stock_real}</Text>
              <Text style={styles.normalStockUnit}> uds.</Text>
            </View>
          )}
        </View>
      </View>
    </Pressable>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.background.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.background.surfaceMuted,
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 48,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  cardPressed: {
    backgroundColor: '#F8FAFC',
  },
  leftColumn: {
    flex: 1,
    paddingRight: 12,
  },
  articleName: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text.primary,
  },
  detailsSubtitle: {
    fontSize: 12,
    color: colors.text.muted,
    marginTop: 4,
  },
  rightColumn: {
    alignItems: 'flex-end',
    justifyContent: 'space-between',
  },
  stockBox: {
    marginTop: 8,
  },
  zeroStockRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  zeroStockText: {
    fontSize: 13,
    fontWeight: '800',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    color: '#DC2626',
  },
  normalStockRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  normalStockNumber: {
    fontSize: 14,
    fontWeight: '800',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    color: colors.text.primary,
  },
  normalStockUnit: {
    fontSize: 12,
    fontWeight: '400',
    color: colors.text.muted,
  },
});
