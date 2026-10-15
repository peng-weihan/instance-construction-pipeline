// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package types_test

import (
	"testing"

	"github.com/google/cel-go/common/types"
	"github.com/google/cel-go/common/types/ref"
	"github.com/google/cel-go/common/types/traits"
	canonicaltypes "cel.dev/cel-go/common/types"
	canonicalref "cel.dev/cel-go/common/types/ref"
	canonicaltraits "cel.dev/cel-go/common/types/traits"
)

func TestTypeAliases(t *testing.T) {
	var b types.Bool = types.True
	var cb canonicaltypes.Bool = b
	if cb != canonicaltypes.True {
		t.Fatalf("expected True")
	}

	var val ref.Val = b
	var cval canonicalref.Val = b
	var cval2 canonicalref.Val = val

	if cval.Type() != canonicaltypes.BoolType {
		t.Fatalf("expected BoolType")
	}
	_ = cval2

	var comparer traits.Comparer = b
	var ccomparer canonicaltraits.Comparer = comparer
	_ = ccomparer
}
