import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  FlatList,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { useMobileDataClient } from '../context/DataContext';
import { ArticuloAuditorView } from '../types/article';
import { CatalogItemCard } from '../components/catalog/CatalogItemCard';
import { CatalogFilterSheet, CatalogFilterState } from '../components/catalog/CatalogFilterSheet';
import { Icon } from '../components/ui/Icon';
import { colors } from '../utils/designTokens';

interface CatalogScreenProps {
  onSelectArticle: (articleId: string) => void;
}

export const CatalogScreen: React.FC<CatalogScreenProps> = ({ onSelectArticle }) => {
  const client = useMobileDataClient();

  const [search, setSearch] = useState('');
  const [items, setItems] = useState<ArticuloAuditorView[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filters, setFilters] = useState<CatalogFilterState>({
    status: 'all',
    criticalOnly: false,
  });
  const [isFilterSheetOpen, setIsFilterSheetOpen] = useState(false);

  const loadCatalog = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await client.getArticleCatalog({
        search: search.trim() || undefined,
        status: filters.status,
        criticalOnly: filters.criticalOnly,
      });
      setItems(res.items);
    } catch {
      // Ignored
    } finally {
      setIsLoading(false);
    }
  }, [client, search, filters]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  const hasActiveFilters = filters.status !== 'all' || filters.criticalOnly;

  return (
    <View style={styles.container}>
      {/* Title */}
      <View style={styles.titleContainer}>
        <Text style={styles.screenTitle}>Catálogo de artículos</Text>
      </View>

      {/* Search & Filter Row */}
      <View style={styles.searchRow}>
        <View style={styles.searchBox}>
          <Icon name="search" size={16} color={colors.text.disabled} />
          <TextInput
            style={styles.searchInput}
            value={search}
            onChangeText={setSearch}
            placeholder="Buscá por código o nombre..."
            placeholderTextColor={colors.text.disabled}
            autoCapitalize="none"
          />
          {search.length > 0 && (
            <Pressable onPress={() => setSearch('')} hitSlop={8}>
              <Icon name="x" size={16} color={colors.text.disabled} />
            </Pressable>
          )}
        </View>

        {/* Filter Button */}
        <Pressable
          onPress={() => setIsFilterSheetOpen(true)}
          style={({ pressed }) => [
            styles.filterBtn,
            hasActiveFilters && styles.filterBtnActive,
            pressed && styles.filterBtnPressed,
          ]}
        >
          <Icon
            name="list-filter"
            size={18}
            color={hasActiveFilters ? colors.primary[500] : colors.text.secondary}
          />
          {hasActiveFilters && <View style={styles.filterDot} />}
        </Pressable>
      </View>

      {/* Results Counter Row */}
      <View style={styles.counterRow}>
        <Text style={styles.counterText}>
          {items.length} {items.length === 1 ? 'resultado' : 'resultados'}
        </Text>
      </View>

      {/* Catalog List */}
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator color={colors.primary[500]} size="small" />
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id_articulo}
          renderItem={({ item }) => (
            <CatalogItemCard
              item={item}
              onPress={() => onSelectArticle(item.id_articulo)}
            />
          )}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyTitle}>No se encontraron artículos</Text>
              <Text style={styles.emptySubtitle}>
                Probá con otro término de búsqueda o restablecé los filtros.
              </Text>
            </View>
          }
        />
      )}

      {/* Filter Bottom Sheet */}
      <CatalogFilterSheet
        isVisible={isFilterSheetOpen}
        onClose={() => setIsFilterSheetOpen(false)}
        filters={filters}
        onApplyFilters={setFilters}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.base,
  },
  titleContainer: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 4,
  },
  screenTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.text.primary,
  },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 16,
    marginTop: 8,
  },
  searchBox: {
    flex: 1,
    height: 48,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: colors.text.primary,
    marginLeft: 8,
  },
  filterBtn: {
    width: 48,
    height: 48,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  filterBtnActive: {
    borderColor: colors.primary[500],
    backgroundColor: colors.primary[50],
  },
  filterBtnPressed: {
    backgroundColor: '#F1F5F9',
  },
  filterDot: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.primary[500],
  },
  counterRow: {
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  counterText: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.text.muted,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 32,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyContainer: {
    paddingVertical: 48,
    alignItems: 'center',
  },
  emptyTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text.secondary,
  },
  emptySubtitle: {
    fontSize: 12,
    color: colors.text.disabled,
    textAlign: 'center',
    marginTop: 4,
    paddingHorizontal: 32,
  },
});
