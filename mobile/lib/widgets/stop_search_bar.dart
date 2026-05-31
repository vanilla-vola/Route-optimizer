import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';

import '../api/api_client.dart';
import '../models/models.dart';
import '../providers/app_providers.dart';

class StopSearchBar extends ConsumerStatefulWidget {
  const StopSearchBar({super.key});

  @override
  ConsumerState<StopSearchBar> createState() => _StopSearchBarState();
}

class _StopSearchBarState extends ConsumerState<StopSearchBar> {
  final _controller = TextEditingController();
  Timer? _debounce;
  List<PlaceSuggestionDto> _results = const [];
  bool _loading = false;
  String? _error;
  bool _showResults = false;

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _clearRoute() {
    ref.read(routeOrderProvider.notifier).state = null;
    ref.read(orderedStopsProvider.notifier).state = null;
  }

  void _onQueryChanged(String value) {
    _debounce?.cancel();
    final trimmed = value.trim();
    if (trimmed.length < 2) {
      setState(() {
        _results = const [];
        _loading = false;
        _error = null;
        _showResults = false;
      });
      return;
    }

    _debounce = Timer(const Duration(milliseconds: 300), () async {
      setState(() {
        _loading = true;
        _error = null;
      });
      try {
        final places =
            await ref.read(apiClientProvider).searchPlaces(trimmed);
        if (!mounted) return;
        setState(() {
          _results = places;
          _showResults = true;
        });
      } catch (error) {
        if (!mounted) return;
        setState(() {
          _results = const [];
          _error = formatApiError(error);
          _showResults = true;
        });
      } finally {
        if (mounted) setState(() => _loading = false);
      }
    });
  }

  void _selectPlace(PlaceSuggestionDto place) {
    ref.read(stopsProvider.notifier).addStop(
          StopDto(lat: place.lat, lng: place.lng, name: place.name),
        );
    _clearRoute();
    ref.read(mapFocusProvider.notifier).state =
        LatLng(place.lat, place.lng);
    _controller.clear();
    setState(() {
      _results = const [];
      _showResults = false;
      _error = null;
    });
    FocusScope.of(context).unfocus();
  }

  @override
  Widget build(BuildContext context) {
    final apiOnline = ref.watch(apiOnlineProvider).value ?? true;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _controller,
          enabled: apiOnline,
          decoration: InputDecoration(
            labelText: 'Search for a stop',
            hintText: 'Address, landmark, city…',
            prefixIcon: const Icon(Icons.search),
            suffixIcon: _loading
                ? const Padding(
                    padding: EdgeInsets.all(12),
                    child: SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  )
                : _controller.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _controller.clear();
                          _onQueryChanged('');
                        },
                      )
                    : null,
            border: const OutlineInputBorder(),
            isDense: true,
          ),
          onChanged: _onQueryChanged,
          onTap: () {
            if (_results.isNotEmpty) {
              setState(() => _showResults = true);
            }
          },
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              _error!,
              style: TextStyle(
                color: Theme.of(context).colorScheme.error,
                fontSize: 13,
              ),
            ),
          ),
        if (_showResults && !_loading && _controller.text.trim().length >= 2)
          Material(
            elevation: 4,
            borderRadius: BorderRadius.circular(8),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 200),
              child: _results.isEmpty
                  ? const ListTile(
                      dense: true,
                      title: Text('No places found'),
                    )
                  : ListView.separated(
                      shrinkWrap: true,
                      itemCount: _results.length,
                      separatorBuilder: (context, index) =>
                          const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final place = _results[index];
                        return ListTile(
                          dense: true,
                          title: Text(
                            place.name,
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          subtitle: place.subtitle.isNotEmpty
                              ? Text(
                                  place.subtitle,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                )
                              : null,
                          onTap: () => _selectPlace(place),
                        );
                      },
                    ),
            ),
          ),
      ],
    );
  }
}
