import React from 'react';
import { View, TextInput, Pressable, Text, StyleSheet } from 'react-native';
import { Icon } from '../ui/Icon';
import { colors } from '../../utils/designTokens';

interface SearchScannerBarProps {
  query: string;
  onChangeQuery: (text: string) => void;
  onSearch: () => void;
  onOpenScanner: () => void;
  isLoading?: boolean;
}

export const SearchScannerBar: React.FC<SearchScannerBarProps> = ({
  query,
  onChangeQuery,
  onSearch,
  onOpenScanner,
  isLoading,
}) => {
  return (
    <View style={styles.container}>
      {/* Search Input Box */}
      <View style={styles.inputWrapper}>
        <Icon name="search" size={16} color={colors.text.disabled} />
        <TextInput
          style={styles.input}
          value={query}
          onChangeText={onChangeQuery}
          placeholder="Código o nombre..."
          placeholderTextColor={colors.text.disabled}
          returnKeyType="search"
          onSubmitEditing={onSearch}
          autoCapitalize="none"
          autoCorrect={false}
        />
      </View>

      {/* Camera Barcode Trigger Button */}
      <Pressable
        onPress={onOpenScanner}
        style={({ pressed }) => [styles.iconButton, pressed && styles.iconButtonPressed]}
        hitSlop={6}
      >
        <Icon name="camera" size={20} color={colors.text.secondary} />
      </Pressable>

      {/* Primary Buscar Action Button */}
      <Pressable
        onPress={onSearch}
        disabled={isLoading || !query.trim()}
        style={({ pressed }) => [
          styles.searchButton,
          pressed && styles.searchButtonPressed,
          (!query.trim() || isLoading) && styles.searchButtonDisabled,
        ]}
      >
        <Text style={styles.searchButtonText}>Buscar</Text>
      </Pressable>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 8,
  },
  inputWrapper: {
    flex: 1,
    height: 48,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
  },
  input: {
    flex: 1,
    fontSize: 14,
    color: colors.text.primary,
    marginLeft: 8,
  },
  iconButton: {
    width: 48,
    height: 48,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconButtonPressed: {
    backgroundColor: '#F1F5F9',
  },
  searchButton: {
    height: 48,
    paddingHorizontal: 16,
    backgroundColor: colors.primary[500],
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchButtonPressed: {
    backgroundColor: colors.primary[600],
  },
  searchButtonDisabled: {
    backgroundColor: colors.text.disabled,
  },
  searchButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
